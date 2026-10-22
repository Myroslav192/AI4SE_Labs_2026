"""The actual LangGraph: deterministic nodes, four LLM agents and a bounded loop."""
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .corpus import chunk_documents, ground_candidate, load_corpus, normalize
from .llm import write_json
from .prompts import ADJUDICATE_REVIEW, AUDIT_DOCUMENT, AUDIT_GLOBAL, AUDIT_REJECTIONS, AUDIT_TRACEABILITY, EXTRACT, REFINE, REPAIR_EVIDENCE, REPAIR_DISPOSITIONS, REPAIR_INTERPRETATIONS
from .schemas import Candidate, CandidateText, Chunk, ConsistencyAudit, CoveragePatch, Document, DocumentAudit, Extraction, IncrementalPatch, InterpretationRepairs, Issue, QuoteRepairs, Requirement, ReviewAdjudication, ReviewFeedback, Specification, TraceabilityAudit
from .validation import validate_specification

ALLOWED_MODELS = {"gpt-6-luna", "gpt-5.6-luna", "gpt-5.4-nano", "gpt-5-nano", "gpt-5-mini", "gpt-4.1-nano", "gpt-4o-mini"}


@dataclass(frozen=True)
class Config:
    input_dir: Path
    output_dir: Path
    extractor_model: str = "gpt-4o-mini"
    editor_model: str = "gpt-5-mini"
    reviewer_model: str = "gpt-5-nano"
    language: str = "English"
    max_revisions: int = 2
    chunk_chars: int = 12000
    review_workers: int = 4
    repair_batch_size: int = 24
    rescan_sources: bool = False
    review_feedback: Path | None = None
    source_audit_rounds: int | None = None

    def validate(self):
        models = [self.extractor_model, self.editor_model, self.reviewer_model]
        if len(set(models)) != 3:
            raise ValueError("ANS4 requires three different models, one for each agent.")
        if not set(models).issubset(ALLOWED_MODELS):
            raise ValueError("Select models only from the assignment's permitted list.")
        if self.max_revisions < 0 or self.max_revisions > 10:
            raise ValueError("max_revisions must be between 0 and 10.")
        if self.chunk_chars < 500:
            raise ValueError("chunk_chars must be at least 500.")
        if not 1 <= self.review_workers <= 8:
            raise ValueError("review_workers must be between 1 and 8.")
        if not 0 <= self.repair_batch_size <= 100:
            raise ValueError("repair_batch_size must be between 0 and 100; 0 disables targeted repair.")
        if self.output_dir.resolve().is_relative_to(self.input_dir.resolve()):
            raise ValueError("Output must be outside the input directory to avoid ingesting generated files.")
        if self.review_feedback is not None and not self.review_feedback.is_file():
            raise ValueError("The optional review-feedback JSON file does not exist.")
        if self.source_audit_rounds is not None and not 1 <= self.source_audit_rounds <= 11:
            raise ValueError("source_audit_rounds must be between 1 and 11.")


class State(TypedDict, total=False):
    documents: list[Document]
    chunks: list[Chunk]
    candidates: list[Candidate]
    ignored: list[dict]
    specification: Specification
    revision: int
    issues: list[Issue]
    history: list[dict]
    review_passed: bool
    result_path: str
    source_audits_done: bool
    source_audit_count: int
    traceability_count: int
    external_feedback_applied: bool


class Network:
    def __init__(self, config: Config, client):
        config.validate()
        self.config, self.client = config, client

    def build(self):
        graph = StateGraph(State)
        graph.add_node("load_documents", self.load)
        graph.add_node("extract_requirements", self.extract)
        graph.add_node("refine_requirements", self.refine)
        graph.add_node("review_requirements", self.review)
        graph.add_node("audit_traceability", self.audit_traceability)
        graph.add_node("validate_structure", self.validate)
        graph.add_node("export_document", self.export)
        graph.add_edge(START, "load_documents")
        graph.add_edge("load_documents", "extract_requirements")
        graph.add_edge("extract_requirements", "refine_requirements")
        graph.add_edge("refine_requirements", "review_requirements")
        graph.add_edge("review_requirements", "audit_traceability")
        graph.add_edge("audit_traceability", "validate_structure")
        graph.add_conditional_edges("validate_structure", self.route,
                                   {"revise": "refine_requirements", "export": "export_document"})
        graph.add_edge("export_document", END)
        return graph.compile()

    def load(self, state: State):
        documents, skipped = load_corpus(self.config.input_dir)
        if skipped:
            raise ValueError("Unsupported files would be omitted. Convert or remove them first: " + ", ".join(skipped))
        chunks = chunk_documents(documents, self.config.chunk_chars)
        output = self.config.output_dir
        manifest = []
        for document in documents:
            source_path = output / "sources" / f"{document.id}.txt"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(document.text, encoding="utf-8")
            manifest.append(dict(id=document.id, path=document.path, sha256=document.sha256,
                                 characters=len(document.text), lines=len(document.text.splitlines()),
                                 chunks=sum(chunk.document_id == document.id for chunk in chunks)))
        write_json(output / "source_manifest.json", dict(documents=manifest, skipped_files=skipped))
        print(f"Loaded {len(documents)} documents in {len(chunks)} chunks.", flush=True)
        return dict(documents=documents, chunks=chunks, candidates=[], ignored=[], history=[], revision=-1,
                    source_audits_done=False)

    @staticmethod
    def numbered(chunk: Chunk) -> str:
        return "\n".join(f"{line}: {text}" for line, text in enumerate(chunk.text.splitlines(), chunk.start_line))

    def grounded_candidates(self, items, document, chunk, model, role):
        # Preserve the complete extraction. A quotation problem cannot cause
        # another candidate's statement to disappear during regeneration.
        items = [item.model_copy() for item in items]
        for attempt in range(3):
            grounded, rejected = [], []
            for index, item in enumerate(items):
                try:
                    grounded.append(ground_candidate(item, document, chunk, "pending"))
                except ValueError as exc:
                    rejected.append(dict(candidate_index=index, candidate=item.model_dump(), error=str(exc)))
            if not rejected:
                return grounded
            if attempt == 2:
                raise ValueError(f"Evidence grounding failed after extraction and two repair attempts: {chunk.id}")
            repairs = self.client.invoke(role + "_evidence_repair", self.config.editor_model, REPAIR_EVIDENCE,
                dict(numbered_source=self.numbered(chunk), rejected_candidates=rejected, attempt=attempt + 1), QuoteRepairs, 8000)
            expected = {item["candidate_index"] for item in rejected}
            actual = [repair.candidate_index for repair in repairs.repairs]
            if set(actual) != expected or len(actual) != len(expected):
                raise ValueError(f"Evidence repair returned incorrect candidate indices: {chunk.id}")
            for repair in repairs.repairs:
                items[repair.candidate_index] = items[repair.candidate_index].model_copy(update={"evidence_quote": repair.evidence_quote})

    def extract(self, state: State):
        documents = {document.id: document for document in state["documents"]}
        candidates, ignored, seen = [], [], set()
        for chunk in state["chunks"]:
            document = documents[chunk.document_id]
            extracted = self.client.invoke("extract", self.config.extractor_model, EXTRACT,
                dict(document_id=document.id, source_path=document.path, chunk_id=chunk.id,
                     numbered_source=self.numbered(chunk), quotation_feedback=""), Extraction)
            additions = self.grounded_candidates(extracted.candidates, document, chunk, self.config.extractor_model, "extract")
            for candidate in additions:
                fingerprint = (candidate.document_id, normalize(candidate.statement).casefold(), normalize(candidate.evidence_quote))
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    candidates.append(candidate.model_copy(update={"id": f"CAND-{len(candidates) + 1:05d}"}))
            ignored.append(dict(chunk_id=chunk.id, summary=extracted.ignored_content_summary))
        if not candidates:
            raise ValueError("Extraction found no requirements; inspect the inputs and model output.")
        write_json(self.config.output_dir / "candidates.json", [candidate.model_dump() for candidate in candidates])
        write_json(self.config.output_dir / "ignored_content.json", ignored)
        print(f"Extracted {len(candidates)} source-grounded candidates.", flush=True)
        return dict(candidates=candidates, ignored=ignored)

    def refine(self, state: State):
        revision = state["revision"] + 1
        if "specification" in state and self.config.repair_batch_size:
            # Preserve already-correct paragraphs instead of asking a long
            # complete regeneration to remember every previously accepted detail.
            specification = state["specification"].model_copy(deep=True)
            errors = [issue for issue in state.get("issues", []) if issue.severity == "error"]
            affected = {identifier for issue in errors for identifier in issue.candidate_ids}
            if errors and all(issue.candidate_ids for issue in errors):
                write_json(self.config.output_dir / f"draft-{revision:02d}-before-coverage.json", specification.model_dump())
                for entry in [*specification.requirements, *specification.blacklist]:
                    entry.candidate_ids = [identifier for identifier in entry.candidate_ids if identifier not in affected]
                specification = self.repair_dispositions(specification, state["candidates"], revision, errors)
                notes = [issue for issue in state.get("issues", []) if issue.severity == "warning"
                         and issue.category in {"completeness", "description"} and issue.candidate_ids]
                if notes:
                    advisory_ids = {identifier for issue in notes for identifier in issue.candidate_ids}
                    for entry in [*specification.requirements, *specification.blacklist]:
                        entry.candidate_ids = [identifier for identifier in entry.candidate_ids if identifier not in advisory_ids]
                    specification = self.repair_dispositions(specification, state["candidates"], revision, notes,
                                                            artifact_label="advisory-patches")
                specification.requirements = [entry for entry in specification.requirements if entry.candidate_ids]
                specification.blacklist = [entry for entry in specification.blacklist if entry.candidate_ids]
                write_json(self.config.output_dir / f"draft-{revision:02d}.json", specification.model_dump())
                return dict(specification=specification, revision=revision)
        payload = dict(output_language=self.config.language,
                       sources=[document.model_dump() for document in state["documents"]],
                       candidates=[candidate.model_dump() for candidate in state["candidates"]],
                       previous_specification=state["specification"].model_dump() if "specification" in state else None,
                       feedback=[issue.model_dump() for issue in state.get("issues", [])])
        specification = self.client.invoke("refine", self.config.editor_model, REFINE, payload, Specification, 50000)
        write_json(self.config.output_dir / f"draft-{revision:02d}-before-coverage.json", specification.model_dump())
        if self.config.repair_batch_size:
            specification = self.repair_dispositions(specification, state["candidates"], revision)
        write_json(self.config.output_dir / f"draft-{revision:02d}.json", specification.model_dump())
        return dict(specification=specification, revision=revision)

    def repair_dispositions(self, specification, candidates, revision, review_findings=None, artifact_label="coverage-patches"):
        specification = specification.model_copy(deep=True)
        occurrences = Counter(item for entry in [*specification.requirements, *specification.blacklist] for item in entry.candidate_ids)
        pending = [candidate for candidate in candidates if occurrences[candidate.id] != 1]
        if not pending:
            return specification
        pending_ids = {candidate.id for candidate in pending}
        # Remove ambiguous bindings only; the editor must explicitly decide each
        # one again. No deterministic semantic guess assigns a source to a topic.
        for entry in [*specification.requirements, *specification.blacklist]:
            entry.candidate_ids = [item for item in entry.candidate_ids if item not in pending_ids]
        specification.blacklist = [entry for entry in specification.blacklist if entry.candidate_ids]
        patches = []
        batch_size = self.config.repair_batch_size
        for start in range(0, len(pending), batch_size):
            batch = pending[start:start + batch_size]
            expected = {candidate.id for candidate in batch}
            feedback = ""
            for attempt in range(3):
                indexed_specification = specification.model_dump()
                indexed_specification["requirements"] = [dict(target_index=index, **entry)
                    for index, entry in enumerate(indexed_specification["requirements"])]
                payload = dict(existing_specification=indexed_specification,
                               pending_candidates=[candidate.model_dump() for candidate in batch],
                               correction_feedback=feedback, attempt=attempt)
                prompt = REPAIR_DISPOSITIONS
                if review_findings:
                    payload["review_findings"] = [issue.model_dump() for issue in review_findings
                        if expected.intersection(issue.candidate_ids)]
                    prompt += ("\nThis is an incremental revision. Address every supplied review finding. "
                        "Preserve already-supported details and exact thresholds, standards, versions and conditions. "
                        "Different source candidates can support different clauses of a merged requirement. "
                        "Do not remove a detail supported by another source merely because one source omits it. "
                        "Correct a wrong binding by moving the candidate, not by stripping valid details from the retained requirement. "
                        "When an old paragraph had several unrelated needs, split them into cohesive requirements. "
                        "Suggested fixes may contain illustrative extras: only source-supported obligations are authoritative. "
                        "For an existing target, DO NOT rewrite or summarize its paragraph. Supply exact "
                        "replacements (old_text must occur literally and uniquely) only for erroneous fragments, "
                        "and append_explanation containing only genuinely new source-supported sentences. "
                        "Python preserves every other character of the original paragraph. Empty replacements "
                        "and empty append_explanation are valid for a provenance-only reassignment. "
                        "Never use 'preserving the existing requirements...' as a substitute for their text. "
                        "For target_index=-1 use no replacements and put the complete new paragraph in append_explanation. "
                        "Keep unresolved source decisions explicit rather than inventing a decision.\n")
                patch = self.client.invoke("repair_dispositions", self.config.editor_model, prompt,
                                          payload, IncrementalPatch if review_findings else CoveragePatch, 20000)
                returned = [item for entry in [*patch.requirements, *patch.blacklist] for item in entry.candidate_ids]
                targets = [entry.target_index for entry in patch.requirements if entry.target_index >= 0]
                problems = []
                if set(returned) != expected or len(returned) != len(expected):
                    problems.append(f"Use each pending ID once. Missing={sorted(expected - set(returned))}; "
                                    f"unexpected={sorted(set(returned) - expected)}; duplicates="
                                    f"{[item for item, count in Counter(returned).items() if count > 1]}")
                if any(not entry.candidate_ids for entry in [*patch.requirements, *patch.blacklist]):
                    problems.append("Every returned update or rejection must resolve at least one pending ID.")
                if len(targets) != len(set(targets)):
                    problems.append("Return at most one update per existing target_index.")
                if any(entry.target_index < -1 or entry.target_index >= len(specification.requirements) for entry in patch.requirements):
                    problems.append("target_index must be -1 or a valid existing requirement index.")
                if review_findings:
                    for entry in patch.requirements:
                        if entry.target_index == -1:
                            if entry.replacements or len(entry.append_explanation.split()) < 25:
                                problems.append("New requirements need a complete paragraph and no replacements.")
                        elif 0 <= entry.target_index < len(specification.requirements):
                            text = specification.requirements[entry.target_index].explanation
                            for replacement in entry.replacements:
                                if not replacement.old_text or text.count(replacement.old_text) != 1:
                                    problems.append("Each old_text must match one exact unique fragment of the target paragraph.")
                                    break
                                text = text.replace(replacement.old_text, replacement.new_text, 1)
                if not problems:
                    break
                feedback = "\n".join(problems)
                if attempt == 2:
                    raise ValueError("Targeted disposition repair did not satisfy its exact ID contract: " + feedback)
            for update in patch.requirements:
                if review_findings:
                    text = "" if update.target_index == -1 else specification.requirements[update.target_index].explanation
                    for replacement in update.replacements:
                        text = text.replace(replacement.old_text, replacement.new_text, 1)
                    fields = update.model_dump(exclude={"target_index", "replacements", "append_explanation"})
                    fields["explanation"] = " ".join((text.strip(), update.append_explanation.strip())).strip()
                else:
                    fields = update.model_dump(exclude={"target_index"})
                if update.target_index == -1:
                    specification.requirements.append(Requirement(**fields))
                else:
                    previous = specification.requirements[update.target_index]
                    fields["candidate_ids"] = previous.candidate_ids + update.candidate_ids
                    specification.requirements[update.target_index] = Requirement(**fields)
            specification.blacklist.extend(patch.blacklist)
            patches.append(dict(pending_ids=sorted(expected), patch=patch.model_dump()))
        write_json(self.config.output_dir / f"{artifact_label}-{revision:02d}.json", patches)
        print(f"Targeted repair resolved {len(pending)} omitted or ambiguously assigned candidates.", flush=True)
        return specification

    def review(self, state: State):
        specification = state["specification"].model_dump()
        candidates, issues = list(state["candidates"]), []
        seen = {(candidate.document_id, normalize(candidate.statement).casefold(), normalize(candidate.evidence_quote))
                for candidate in candidates}
        additions = 0
        def audit_one(document):
            # Independent comparison to EVERY full source, rather than just the
            # extractor's summaries, addresses omissions in the first LLM stage.
            full_chunk = Chunk(id=f"{document.id}-AUDIT", document_id=document.id, start_line=1,
                               end_line=len(document.text.splitlines()), text=document.text)
            source_candidates = [candidate for candidate in state["candidates"] if candidate.document_id == document.id]
            source_ids = {candidate.id for candidate in source_candidates}
            focused_specification = dict(specification)
            focused_specification["open_questions"] = [question for question in specification["open_questions"]
                if source_ids.intersection(question["candidate_ids"])]
            dispositions = [dict(candidate_id=candidate.id,
                accepted_in=[entry["name"] for entry in specification["requirements"] if candidate.id in entry["candidate_ids"]],
                rejected_in=[dict(name=entry["name"], reason=entry["reason"]) for entry in specification["blacklist"]
                             if candidate.id in entry["candidate_ids"]]) for candidate in source_candidates]
            audit = self.client.invoke("review_source", self.config.editor_model, AUDIT_DOCUMENT,
                dict(document=document.model_dump(), specification=focused_specification,
                     source_candidate_dispositions=dispositions,
                     existing_source_candidates=[candidate.model_dump() for candidate in source_candidates],
                     quotation_feedback=""), DocumentAudit, 16000)
            missing = self.grounded_candidates(audit.missing_candidates, document, full_chunk, self.config.reviewer_model, "review")
            return audit, missing

        # Source audits are independent. Collect in input order so completion
        # timing does not change candidate numbering or reconciliation order.
        audits = []
        rescan = self.config.rescan_sources and (self.config.source_audit_rounds is None
                                                or state["revision"] < self.config.source_audit_rounds)
        if not state.get("source_audits_done", False) or rescan:
            with ThreadPoolExecutor(max_workers=self.config.review_workers) as pool:
                audits = list(pool.map(audit_one, state["documents"]))
        for document, (audit, missing) in zip(state["documents"], audits):
            issues.extend(audit.issues)
            for candidate in missing:
                fingerprint = (candidate.document_id, normalize(candidate.statement).casefold(), normalize(candidate.evidence_quote))
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                candidate = candidate.model_copy(update={"id": f"CAND-{len(candidates) + 1:05d}"})
                candidates.append(candidate)
                additions += 1
                issues.append(Issue(category="completeness", severity="error",
                    description=f"Independent review discovered {candidate.id}: {candidate.statement}",
                    suggested_fix="Integrate this new grounded candidate, merging only if semantically equivalent.",
                    candidate_ids=[candidate.id]))
        global_audit = self.client.invoke("review_global", self.config.reviewer_model, AUDIT_GLOBAL,
            dict(specification=specification, candidates=[candidate.model_dump() for candidate in candidates]), ConsistencyAudit, 16000)
        issues.extend(global_audit.issues)
        if issues:
            issues = self.adjudicate_findings(issues, specification, candidates, state)
        write_json(self.config.output_dir / "candidates.json", [candidate.model_dump() for candidate in candidates])
        print(f"Review {state['revision']}: {len(issues)} findings; {additions} newly discovered candidates.", flush=True)
        return dict(candidates=candidates, issues=issues, source_audits_done=True, source_audit_count=len(audits))

    def adjudicate_findings(self, issues, specification, candidates, state):
        feedback = ""
        expected = set(range(len(issues)))
        for attempt in range(3):
            result = self.client.invoke("adjudicate_review", self.config.editor_model, ADJUDICATE_REVIEW,
                dict(specification=specification, candidates=[candidate.model_dump() for candidate in candidates],
                     sources=[document.model_dump() for document in state["documents"]],
                     issues=[dict(issue_index=index, **issue.model_dump()) for index, issue in enumerate(issues)],
                     correction_feedback=feedback), ReviewAdjudication, 24000)
            actual = [decision.issue_index for decision in result.decisions]
            if set(actual) == expected and len(actual) == len(expected):
                break
            feedback = f"Assess exactly these issue indices once each: {sorted(expected)}. Returned: {actual}"
        else:
            raise ValueError("Review adjudication did not assess exactly the supplied issue indices.")
        decisions = {decision.issue_index: decision for decision in result.decisions}
        write_json(self.config.output_dir / f"review-decisions-{state['revision']:02d}.json",
            [dict(issue=issue.model_dump(), **decisions[index].model_dump()) for index, issue in enumerate(issues)])
        return [issue for index, issue in enumerate(issues) if decisions[index].retain]

    def audit_traceability(self, state: State):
        documents = {document.id: document for document in state["documents"]}
        candidate_by_id = {candidate.id: candidate for candidate in state["candidates"]}
        dispositions = {}
        for kind, entries in (("accepted", state["specification"].requirements),
                              ("rejected", state["specification"].blacklist)):
            for entry in entries:
                for identifier in entry.candidate_ids:
                    dispositions.setdefault(identifier, []).append(dict(disposition=kind, entry=entry.model_dump()))
        pairs = []
        for candidate in state["candidates"]:
            assigned = dispositions.get(candidate.id, [])
            if len(assigned) != 1:
                continue  # The deterministic coverage validator reports these IDs.
            lines = documents[candidate.document_id].text.splitlines()
            context = "\n".join(lines[max(0, candidate.start_line - 4):candidate.end_line + 3])
            other_evidence = [candidate_by_id[identifier].model_dump() for identifier in assigned[0]["entry"]["candidate_ids"]
                              if identifier in candidate_by_id and identifier != candidate.id]
            pairs.append(dict(candidate=candidate.model_dump(), source_context=context,
                              other_supporting_evidence=other_evidence, **assigned[0]))

        stabilized = state.get("source_audit_count", 0) == 0
        def audit_batch(batch):
            expected = {pair["candidate"]["id"] for pair in batch}
            rejection_batch = stabilized and all(pair["disposition"] == "rejected" for pair in batch)
            prompt = AUDIT_REJECTIONS if rejection_batch else AUDIT_TRACEABILITY
            feedback = ""
            for attempt in range(3):
                result = self.client.invoke("review_traceability", self.config.editor_model, prompt,
                    dict(pairs=batch, scope=state["specification"].scope,
                         open_questions=[question.model_dump() for question in state["specification"].open_questions],
                         correction_feedback=feedback), TraceabilityAudit, 10000)
                actual = [assessment.candidate_id for assessment in result.assessments]
                valid_verdicts = not rejection_batch or all(item.verdict in {"covered", "invalid_rejection"}
                                                            for item in result.assessments)
                if set(actual) == expected and len(actual) == len(expected) and valid_verdicts:
                    return result.assessments
                feedback = ("Return every supplied ID exactly once and no other IDs. "
                            f"Expected={sorted(expected)}; returned={actual}.")
                if rejection_batch and not valid_verdicts:
                    feedback += " These proposals are ALREADY rejected: use covered or invalid_rejection only."
            raise ValueError("Traceability reviewer did not assess exactly the supplied candidate IDs.")

        if stabilized:
            groups = [[pair for pair in pairs if pair["disposition"] == kind] for kind in ("accepted", "rejected")]
            batches = [group[start:start + 20] for group in groups for start in range(0, len(group), 20)]
        else:
            batches = [pairs[start:start + 20] for start in range(0, len(pairs), 20)]
        with ThreadPoolExecutor(max_workers=self.config.review_workers) as pool:
            results = list(pool.map(audit_batch, batches))
        assessments = [assessment for batch in results for assessment in batch]
        issues = list(state["issues"])
        for assessment in assessments:
            if assessment.verdict != "covered":
                issues.append(Issue(category="blacklist" if assessment.verdict == "invalid_rejection" else "provenance",
                    severity="error", description=f"{assessment.candidate_id} / {assessment.verdict}: {assessment.reason}",
                    suggested_fix=assessment.suggested_fix, candidate_ids=[assessment.candidate_id]))
        write_json(self.config.output_dir / f"traceability-{state['revision']:02d}.json",
                   [assessment.model_dump() for assessment in assessments])
        repair_findings = {item.candidate_id: item for item in assessments if item.verdict == "unsupported"}
        # A full-source reviewer may detect a bad quotation even when the
        # pairwise auditor accepts a broad merged requirement. Recheck both.
        for issue in state["issues"]:
            if issue.category == "provenance" and issue.severity == "error":
                for identifier in issue.candidate_ids:
                    if identifier in candidate_by_id and identifier not in repair_findings:
                        from .schemas import CandidateAssessment
                        repair_findings[identifier] = CandidateAssessment(candidate_id=identifier, verdict="unsupported",
                            reason=issue.description, suggested_fix=issue.suggested_fix)
        corrected = self.repair_interpretations(state["candidates"], list(repair_findings.values()), documents, state["revision"])
        write_json(self.config.output_dir / "candidates.json", [candidate.model_dump() for candidate in corrected])
        print(f"Traceability {state['revision']}: assessed {len(assessments)} bindings; "
              f"{sum(item.verdict != 'covered' for item in assessments)} need correction.", flush=True)
        return dict(candidates=corrected, issues=issues, traceability_count=len(assessments))

    def repair_interpretations(self, candidates, assessments, documents, revision):
        unsupported = {item.candidate_id: item for item in assessments if item.verdict == "unsupported"}
        if not unsupported:
            return candidates
        pending = [candidate for candidate in candidates if candidate.id in unsupported]
        repaired = {candidate.id: candidate for candidate in candidates}
        records = []
        for start in range(0, len(pending), 12):
            batch = pending[start:start + 12]
            expected = {candidate.id for candidate in batch}
            feedback = ""
            for attempt in range(3):
                result = self.client.invoke("repair_interpretations", self.config.editor_model, REPAIR_INTERPRETATIONS,
                    dict(candidates=[candidate.model_dump() for candidate in batch],
                         sources=[documents[identifier].model_dump() for identifier in sorted({item.document_id for item in batch})],
                         findings=[unsupported[candidate.id].model_dump() for candidate in batch],
                         correction_feedback=feedback), InterpretationRepairs, 14000)
                actual = [correction.candidate_id for correction in result.corrections]
                if set(actual) != expected or len(actual) != len(expected):
                    feedback = f"Return exactly these IDs once each: {sorted(expected)}. Returned: {actual}"
                    continue
                corrected_batch = []
                try:
                    for correction in result.corrections:
                        previous = repaired[correction.candidate_id]
                        document = documents[previous.document_id]
                        chunk = Chunk(id=f"{document.id}-SEMANTIC-{revision:02d}", document_id=document.id,
                            start_line=1, end_line=len(document.text.splitlines()), text=document.text)
                        text = CandidateText.model_validate(correction.model_dump(exclude={"candidate_id", "reason"}))
                        candidate = ground_candidate(text, document, chunk, previous.id)
                        corrected_batch.append((previous, candidate, correction.reason))
                except ValueError as exc:
                    feedback = f"Every quote must exist literally in the candidate's own document: {exc}"
                    continue
                break
            else:
                raise ValueError("Interpretation repair could not return all candidates with grounded evidence.")
            for previous, candidate, reason in corrected_batch:
                repaired[candidate.id] = candidate
                records.append(dict(before=previous.model_dump(), after=candidate.model_dump(), reason=reason))
        write_json(self.config.output_dir / f"candidate-corrections-{revision:02d}.json", records)
        return [repaired[candidate.id] for candidate in candidates]

    def validate(self, state: State):
        candidates = list(state["candidates"])
        issues = list(state["issues"])
        applied = state.get("external_feedback_applied", False)
        if self.config.review_feedback is not None and not applied:
            feedback = ReviewFeedback.model_validate(json.loads(self.config.review_feedback.read_text(encoding="utf-8")))
            if not 0 <= feedback.apply_at_revision <= self.config.max_revisions:
                raise ValueError("Feedback revision must be within the configured revision budget.")
            if state["revision"] >= feedback.apply_at_revision:
                documents = {document.path: document for document in state["documents"]}
                records = []
                for addition in feedback.additions:
                    if addition.source_path not in documents:
                        raise ValueError("Review feedback refers to a source outside the current corpus.")
                    document = documents[addition.source_path]
                    chunk = Chunk(id=f"{document.id}-FEEDBACK", document_id=document.id, start_line=1,
                                  end_line=len(document.text.splitlines()), text=document.text)
                    candidate = ground_candidate(addition.candidate, document, chunk, f"CAND-{len(candidates) + 1:05d}")
                    existing = next((item for item in candidates if item.document_id == candidate.document_id
                        and normalize(item.statement) == normalize(candidate.statement)
                        and item.evidence_quote == candidate.evidence_quote), None)
                    if existing is None:
                        candidates.append(candidate)
                    else:
                        candidate = existing
                    issues.append(Issue(category="completeness", severity="error",
                        description=f"Source-grounded external review: {addition.reason}",
                        suggested_fix="Reconcile this grounded candidate through the normal editor and audit loop.",
                        candidate_ids=[candidate.id]))
                    records.append(dict(candidate=candidate.model_dump(), reason=addition.reason))
                write_json(self.config.output_dir / "external-review-feedback.json", records)
                write_json(self.config.output_dir / "candidates.json", [candidate.model_dump() for candidate in candidates])
                applied = True
        issues += validate_specification(state["specification"], candidates)
        # Duplicate feedback messages need not inflate the reported finding count.
        issues = list({(issue.category, issue.description): issue for issue in issues}.values())
        passed = not any(issue.severity == "error" for issue in issues)
        review = dict(revision=state["revision"], passed=passed, candidate_count=len(candidates),
                      requirement_count=len(state["specification"].requirements),
                      source_document_audits=state["source_audit_count"],
                      traceability_assessments=state["traceability_count"],
                      issues=[issue.model_dump() for issue in issues])
        write_json(self.config.output_dir / f"review-{state['revision']:02d}.json", review)
        return dict(candidates=candidates, issues=issues, review_passed=passed,
                    external_feedback_applied=applied, history=state["history"] + [review])

    def route(self, state: State):
        return "revise" if not state["review_passed"] and state["revision"] < self.config.max_revisions else "export"

    def export(self, state: State):
        from .render import export_results
        result = export_results(self.config, state, getattr(self.client, "events", []))
        return dict(result_path=str(result))
