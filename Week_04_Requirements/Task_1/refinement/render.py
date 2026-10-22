"""Deterministic identifiers, provenance, coverage ledger and one Markdown SRS."""
from collections import Counter
from datetime import datetime, timezone

from .llm import write_json


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def paragraph(value):
    return " ".join(value.strip().splitlines())


def export_results(config, state, events):
    output = config.output_dir
    spec = state["specification"]
    documents = {document.id: document for document in state["documents"]}
    candidates = {candidate.id: candidate for candidate in state["candidates"]}
    assigned, requirements, blacklist = {}, [], []
    # IDs are generated here, never trusted to model-generated numbering. They
    # are unique within this run; edited corpora can legitimately change them.
    ordered_requirements = sorted(spec.requirements, key=lambda item: (item.kind, item.name.casefold()))
    for number, requirement in enumerate(ordered_requirements, 1):
        identifier = f"REQ-{number:04d}"
        entry = dict(id=identifier, **requirement.model_dump())
        requirements.append(entry)
        for candidate_id in requirement.candidate_ids:
            assigned[candidate_id] = identifier
    for number, rejected in enumerate(sorted(spec.blacklist, key=lambda item: item.name.casefold()), 1):
        identifier = f"BL-{number:04d}"
        blacklist.append(dict(id=identifier, **rejected.model_dump()))
        for candidate_id in rejected.candidate_ids:
            assigned[candidate_id] = identifier

    def source_ids(ids):
        return sorted({candidates[item].document_id for item in ids if item in candidates})

    def citations(ids):
        return ", ".join(f"[{item}](#{item.lower()})" for item in source_ids(ids)) or "UNRESOLVED SOURCE"

    status = "REVIEW PASSED" if state["review_passed"] else "DRAFT — UNRESOLVED REVIEW ERRORS"
    lines = [f"# {cell(spec.title)}", "", f"**Status:** {status}", "",
             f"**Review rounds:** {len(state['history'])}; **revisions:** {state['revision']}; "
             f"**source documents:** {len(documents)}; **accepted requirements:** {len(requirements)}.", "",
             "Review passed means the configured checks found no remaining errors; it is not proof of perfect semantic completeness.", "",
             "## 1. Scope", "", paragraph(spec.scope), "", "## 2. Priority scale", "",
             "| Priority | Meaning |", "|---|---|",
             "| P1 — Essential | Explicitly high, mandatory or critical obligations, including source-stated compliance and operational necessities. |",
             "| P2 — Important | Standard required capabilities without an explicit critical or optional signal. |",
             "| P3 — Optional | Desirable enhancements or explicitly low-priority capabilities. |", "",
             "Priorities are inferred from source evidence and include an individual justification. 'Shall' alone does not establish P1.", "",
             "## 3. Controlled vocabulary", "", "| Term | Definition |", "|---|---|"]
    lines.extend(f"| {cell(term.term)} | {cell(term.definition)} |" for term in spec.glossary)
    lines.extend(["", "## 4. Requirements", ""])
    for requirement in requirements:
        lines.extend([f"### {requirement['id']} — {cell(requirement['name'])}", "",
                      f"**Kind:** {requirement['kind']}. **Priority:** {requirement['priority']}.", "",
                      paragraph(requirement["explanation"]), "",
                      f"**Priority rationale:** {paragraph(requirement['priority_reason'])}", "",
                      f"**Sources:** {citations(requirement['candidate_ids'])}. "
                      f"**Evidence candidates:** {', '.join(requirement['candidate_ids'])}.", ""])
    lines.extend(["## 5. Blacklist: discarded requirements", "",
                  "Duplicates are merged with all their sources; they are not discarded requirements.", ""])
    if not blacklist:
        lines.extend(["No candidate was discarded as conflicting, nonsensical or out of scope in this run.", ""])
    for rejected in blacklist:
        lines.extend([f"### {rejected['id']} — {cell(rejected['name'])}", "",
                      f"**Category:** {rejected['category']}", "",
                      f"**Original proposal:** {paragraph(rejected['statement'])}", "",
                      f"**Reason for rejection:** {paragraph(rejected['reason'])}", "",
                      f"**Sources:** {citations(rejected['candidate_ids'])}. "
                      f"**Evidence candidates:** {', '.join(rejected['candidate_ids'])}.", ""])
    lines.extend(["## 6. Open questions and decisions requiring stakeholder input", ""])
    if not spec.open_questions:
        lines.extend(["No open stakeholder question was recorded by the agents.", ""])
    for number, question in enumerate(spec.open_questions, 1):
        lines.extend([f"### OQ-{number:03d} — {cell(question.question)}", "", paragraph(question.reason), "",
                      f"**Sources:** {citations(question.candidate_ids)}.", ""])
    lines.extend(["## 7. Source register", "",
                  "Paths are relative to the input directory. Evidence line numbers refer to the normalized UTF-8 source copies in `sources/`.", ""])
    for document in documents.values():
        lines.extend([f'<a id="{document.id.lower()}"></a>', f"### {document.id} — {cell(document.path)}", "",
                      f"Original file SHA-256: `{document.sha256}`.", ""])
    lines.extend(["## 8. Candidate disposition and evidence ledger", "",
                  "Every extracted or independently discovered candidate must have one accepted or rejected disposition. "
                  "This measures candidate coverage, not guaranteed coverage of every possible interpretation of the corpus.", "",
                  "| Candidate | Disposition | Source and normalized lines | Literal evidence |", "|---|---|---|---|"])
    for candidate in candidates.values():
        lines.append(f"| {candidate.id} | {assigned.get(candidate.id, 'UNRESOLVED')} | "
                     f"{candidate.document_id}:{candidate.start_line}–{candidate.end_line} | {cell(candidate.evidence_quote)} |")
    lines.extend(["", "## 9. Review status and known limitations", "",
                  f"Final automatic review: **{status}**. Independent coverage audits compared every original source document with the draft. "
                  "A separate traceability agent checks every assigned candidate against the meaning of its source and assigned paragraph. "
                  "Revision rounds review the whole specification and grounded candidate ledger; full source rescans are optional.", ""])
    for issue in state["issues"]:
        lines.append(f"- **{issue.severity.upper()} / {issue.category}:** {paragraph(issue.description)} "
                     f"Suggested action: {paragraph(issue.suggested_fix)}")
    if not state["issues"]:
        lines.append("No outstanding automatic review finding was recorded.")
    lines.extend(["", "Semantic deduplication, conflict resolution and interpretation use LLM judgment and may still require human review. "
                  "Historical product descriptions and stakeholder statements are treated as corpus evidence, not verified present-day facts.", ""])
    path = output / "requirements.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    write_json(output / "requirements.json", dict(title=spec.title, scope=spec.scope,
        glossary=[term.model_dump() for term in spec.glossary], requirements=requirements, blacklist=blacklist,
        open_questions=[question.model_dump() for question in spec.open_questions], review_passed=state["review_passed"]))
    accepted_ids = {item for requirement in spec.requirements for item in requirement.candidate_ids}
    rejected_ids = {item for rejected in spec.blacklist for item in rejected.candidate_ids}
    configured_models = {config.extractor_model, config.editor_model, config.reviewer_model}
    served_models = sorted({event.get("served_model") for event in events if event.get("served_model")})
    metrics = dict(generated_utc=datetime.now(timezone.utc).isoformat(),
        invocation_started_utc=events[0].get("time_utc") if events else None, document_count=len(documents),
        chunk_count=len(state["chunks"]), candidate_count=len(candidates), requirement_count=len(requirements),
        blacklist_count=len(blacklist), disposed_candidate_count=len((accepted_ids | rejected_ids) & candidates.keys()),
        candidate_disposition_coverage=len((accepted_ids | rejected_ids) & candidates.keys()) / len(candidates),
        review_passed=state["review_passed"], review_rounds=len(state["history"]), revisions=state["revision"],
        max_revisions=config.max_revisions, review_workers=config.review_workers, rescan_sources=config.rescan_sources,
        review_feedback=str(config.review_feedback) if config.review_feedback is not None else None,
        source_audit_rounds=config.source_audit_rounds,
        outstanding_errors=sum(issue.severity == "error" for issue in state["issues"]),
        outstanding_warnings=sum(issue.severity == "warning" for issue in state["issues"]),
        traceability_assessments=state["traceability_count"],
        priority_counts=dict(Counter(requirement.priority for requirement in spec.requirements)),
        configured_models=sorted(configured_models), served_models=served_models,
        api_calls=sum(event.get("status") == "completed" for event in events),
        cache_hits=sum(event.get("status") == "cache_hit" for event in events),
        input_tokens=sum(event.get("input_tokens", 0) for event in events),
        output_tokens=sum(event.get("output_tokens", 0) for event in events))
    write_json(output / "metrics.json", metrics)
    write_json(output / "review_history.json", state["history"])
    return path
