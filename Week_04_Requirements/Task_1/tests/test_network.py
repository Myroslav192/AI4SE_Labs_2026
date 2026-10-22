"""Offline tests use explicit test doubles, never substitute for a real API run."""
import os
import json
import shutil
import time
import unittest
from email.message import EmailMessage
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from refinement.corpus import chunk_documents, ground_candidate, load_corpus, read_email
from refinement.llm import AgentClient
from refinement.pipeline import Config, Network
from refinement.schemas import CandidateAssessment, CandidateCorrection, CandidateText, CheckResult, ConsistencyAudit, CoveragePatch, Document, DocumentAudit, Extraction, IncrementalPatch, IncrementalUpdate, InterpretationRepairs, Issue, IssueDecision, QuoteRepair, QuoteRepairs, RejectedRequirement, Requirement, RequirementUpdate, ReviewAdjudication, Specification, TextReplacement, TraceabilityAudit
from refinement.validation import validate_specification

SOURCE = "The system shall export reports in CSV format."
SECOND = "The system shall export reports in Excel format."
EXPLANATION = ("The system shall export generated reports in the formats requested by authorized staff. "
               "The export shall preserve the selected report content and allow staff to obtain the "
               "requested representation for their reporting workflow.")


def text_candidate(statement=SOURCE):
    return CandidateText(name="Report export", statement=statement, kind="functional",
                         priority_hint="unspecified", evidence_quote=statement)


class FakeClient:
    def __init__(self, break_first=False, discover_missing=False):
        self.events, self.editor_calls, self.audit_calls = [], 0, 0
        self.break_first, self.discover_missing = break_first, discover_missing
        self.feedback_received = False

    def invoke(self, role, model, prompt, payload, schema, max_tokens=12000):
        self.events.append(dict(role=role, requested_model=model, served_model="test-double", status="test_double"))
        if schema is Extraction:
            return Extraction(candidates=[text_candidate()], ignored_content_summary="No unrelated material.")
        if schema is Specification:
            self.editor_calls += 1
            self.feedback_received |= bool(payload["feedback"])
            ids = [candidate["id"] for candidate in payload["candidates"]]
            if self.break_first and self.editor_calls == 1:
                ids = []
            return Specification(title="Synthetic test specification", scope="Test export behavior.", glossary=[],
                requirements=[Requirement(name="Export reports", explanation=EXPLANATION, kind="functional", priority="P2",
                                          priority_reason="A standard capability in the synthetic source.", candidate_ids=ids)],
                blacklist=[], open_questions=[])
        if schema is DocumentAudit:
            self.audit_calls += 1
            missing = [text_candidate(SECOND)] if self.discover_missing and self.audit_calls == 1 else []
            return DocumentAudit(missing_candidates=missing, issues=[])
        if schema is ConsistencyAudit:
            return ConsistencyAudit(issues=[])
        if schema is TraceabilityAudit:
            return TraceabilityAudit(assessments=[CandidateAssessment(candidate_id=pair["candidate"]["id"],
                verdict="covered", reason="", suggested_fix="") for pair in payload["pairs"]])
        if schema is ReviewAdjudication:
            return ReviewAdjudication(decisions=[IssueDecision(issue_index=item["issue_index"], retain=True,
                reason="Retain this test finding.") for item in payload["issues"]])
        raise AssertionError(f"Unexpected schema {schema}")


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(os.getenv("REFINER_TEST_TEMP", ".test_work")).resolve()
        self.root = self.temp_root / uuid4().hex
        self.input = self.root / "input"
        self.output = self.root / "output"
        self.input.mkdir(parents=True)
        (self.input / "source.txt").write_text(SOURCE + "\n" + SECOND, encoding="utf-8")

    def tearDown(self):
        target = self.root.resolve()
        if not target.is_relative_to(self.temp_root) or target == self.temp_root:
            raise AssertionError("Unsafe test cleanup path")
        shutil.rmtree(target)

    def execute(self, fake, revisions=2):
        # Disable the editor's local repair here to exercise the OUTER graph loop.
        return Network(Config(self.input, self.output, max_revisions=revisions, repair_batch_size=0), fake).build().invoke({})

    def test_targeted_disposition_repair_retains_existing_sources(self):
        first = self.grounded()
        second = first.model_copy(update={"id": "CAND-00002"})
        spec = Specification(title="Test", scope="Test scope", glossary=[], blacklist=[], open_questions=[],
            requirements=[Requirement(name="Export", explanation=EXPLANATION, kind="functional", priority="P2",
                                      priority_reason="Source request.", candidate_ids=[first.id])])
        update = RequirementUpdate(**spec.requirements[0].model_dump(exclude={"candidate_ids"}),
                                   candidate_ids=[second.id], target_index=0)
        client = SimpleNamespace(invoke=lambda *args: CoveragePatch(requirements=[update], blacklist=[]))
        repaired = Network(Config(self.input, self.output), client).repair_dispositions(spec, [first, second], 0)
        self.assertEqual(repaired.requirements[0].candidate_ids, [first.id, second.id])
        self.assertEqual(spec.requirements[0].candidate_ids, [first.id])

    def grounded(self):
        documents, _ = load_corpus(self.input)
        chunk = chunk_documents(documents)[0]
        return ground_candidate(text_candidate(), documents[0], chunk, "CAND-00001")

    def test_real_compiled_graph_revises_on_deterministic_failure(self):
        fake = FakeClient(break_first=True)
        state = self.execute(fake)
        self.assertTrue(state["review_passed"])
        self.assertEqual(state["revision"], 1)
        self.assertEqual(len(state["history"]), 2)
        self.assertTrue(fake.feedback_received)
        self.assertEqual(fake.editor_calls, 2)

    def test_iteration_limit_exports_explicit_draft(self):
        state = self.execute(FakeClient(break_first=True), revisions=0)
        self.assertFalse(state["review_passed"])
        self.assertIn("DRAFT — UNRESOLVED REVIEW ERRORS", (self.output / "requirements.md").read_text(encoding="utf-8"))

    def test_semantic_binding_failure_triggers_editor_feedback(self):
        class BindingClient(FakeClient):
            def invoke(inner_self, role, model, prompt, payload, schema, max_tokens=12000):
                if schema is TraceabilityAudit and inner_self.editor_calls == 1:
                    return TraceabilityAudit(assessments=[CandidateAssessment(
                        candidate_id=pair["candidate"]["id"], verdict="wrong_requirement",
                        reason="An access-permission candidate was attached to a report requirement.",
                        suggested_fix="Move this candidate to the access-permission requirement.") for pair in payload["pairs"]])
                return super().invoke(role, model, prompt, payload, schema, max_tokens)
        client = BindingClient()
        state = self.execute(client)
        self.assertTrue(state["review_passed"])
        self.assertEqual(state["revision"], 1)
        self.assertTrue(client.feedback_received)
        self.assertEqual([review["traceability_assessments"] for review in state["history"]], [1, 1])

    def test_traceability_audit_cannot_silently_omit_or_invent_ids(self):
        class OmittingClient(FakeClient):
            def invoke(inner_self, role, model, prompt, payload, schema, max_tokens=12000):
                if schema is TraceabilityAudit:
                    return TraceabilityAudit(assessments=[])
                return super().invoke(role, model, prompt, payload, schema, max_tokens)
        with self.assertRaisesRegex(ValueError, "exactly the supplied candidate IDs"):
            self.execute(OmittingClient())

    def test_dismissed_review_finding_retains_an_inspectable_reason(self):
        class AdjudicatingClient(FakeClient):
            def invoke(inner_self, role, model, prompt, payload, schema, max_tokens=12000):
                if schema is ConsistencyAudit:
                    return ConsistencyAudit(issues=[Issue(category="duplicate", severity="error",
                        description="Two source candidates support the same final requirement.",
                        suggested_fix="Remove a source.", candidate_ids=["CAND-00001"])])
                if schema is ReviewAdjudication:
                    return ReviewAdjudication(decisions=[IssueDecision(issue_index=0, retain=False,
                        reason="Multiple source candidates are provenance, not duplicate final requirements.")])
                return super().invoke(role, model, prompt, payload, schema, max_tokens)
        state = self.execute(AdjudicatingClient())
        self.assertTrue(state["review_passed"])
        self.assertEqual(state["revision"], 0)
        decisions = (self.output / "review-decisions-00.json").read_text(encoding="utf-8")
        self.assertIn("provenance", decisions)
        self.assertIn('"retain": false', decisions)

    def test_semantic_evidence_repair_keeps_identity_and_validates_the_new_quote(self):
        documents, _ = load_corpus(self.input)
        candidate = self.grounded().model_copy(update={"statement": SECOND})
        assessment = CandidateAssessment(candidate_id=candidate.id, verdict="unsupported",
            reason="The quoted CSV sentence does not support the Excel statement.",
            suggested_fix="Use the actual Excel sentence in this source.")
        calls = []
        def repair(*args):
            calls.append(args)
            return InterpretationRepairs(corrections=[CandidateCorrection(
                **candidate.model_dump(exclude={"id", "document_id", "chunk_id", "start_line", "end_line", "evidence_quote"}),
                candidate_id=candidate.id, evidence_quote="Invented quotation" if len(calls) == 1 else SECOND,
                reason="The second source sentence supports Excel export.")])
        network = Network(Config(self.input, self.output), SimpleNamespace(invoke=repair))
        result = network.repair_interpretations([candidate], [assessment], {documents[0].id: documents[0]}, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result[0].id, candidate.id)
        self.assertEqual(result[0].document_id, candidate.document_id)
        self.assertEqual(result[0].evidence_quote, SECOND)
        self.assertEqual(result[0].start_line, 2)
        self.assertEqual(candidate.evidence_quote, SOURCE)

    def test_source_finding_repairs_evidence_even_if_pairwise_review_accepts_it(self):
        documents, _ = load_corpus(self.input)
        candidate = self.grounded().model_copy(update={"statement": SECOND})
        specification = Specification(title="Test", scope="Test scope", glossary=[], blacklist=[], open_questions=[],
            requirements=[Requirement(name="Export", explanation=EXPLANATION, kind="functional", priority="P2",
                priority_reason="Source request.", candidate_ids=[candidate.id])])
        source_issue = Issue(category="provenance", severity="error", description="The quote supports CSV, not Excel.",
            suggested_fix="Find the Excel evidence in the same document.", candidate_ids=[candidate.id])
        def invoke(role, model, prompt, payload, schema, max_tokens):
            if schema is TraceabilityAudit:
                return TraceabilityAudit(assessments=[CandidateAssessment(candidate_id=candidate.id,
                    verdict="covered", reason="", suggested_fix="")])
            if schema is InterpretationRepairs:
                return InterpretationRepairs(corrections=[CandidateCorrection(
                    **candidate.model_dump(exclude={"id", "document_id", "chunk_id", "start_line", "end_line", "evidence_quote"}),
                    candidate_id=candidate.id, evidence_quote=SECOND, reason="Corrected quotation.")])
            raise AssertionError(schema)
        result = Network(Config(self.input, self.output), SimpleNamespace(invoke=invoke)).audit_traceability(
            dict(documents=documents, candidates=[candidate], specification=specification, issues=[source_issue], revision=0))
        self.assertEqual(result["candidates"][0].evidence_quote, SECOND)
        self.assertIn(source_issue, result["issues"])  # Editing and re-audit remain mandatory.

    def test_stabilized_audit_separates_rejections_and_reports_invalid_rejection(self):
        documents, _ = load_corpus(self.input)
        first = self.grounded()
        second = first.model_copy(update={"id": "CAND-00002", "statement": SECOND,
            "evidence_quote": SECOND, "start_line": 2, "end_line": 2})
        specification = Specification(title="Test", scope="Report exports.", glossary=[], open_questions=[],
            requirements=[Requirement(name="CSV export", explanation=EXPLANATION, kind="functional", priority="P2",
                priority_reason="Source request.", candidate_ids=[first.id])],
            blacklist=[RejectedRequirement(name="Excel export", statement=SECOND, category="out_of_scope",
                reason="This feature was mistakenly considered outside reporting scope.", candidate_ids=[second.id])])
        dispositions = []
        def invoke(role, model, prompt, payload, schema, max_tokens):
            kinds = {pair["disposition"] for pair in payload["pairs"]}
            self.assertEqual(len(kinds), 1)
            kind = next(iter(kinds))
            dispositions.append(kind)
            return TraceabilityAudit(assessments=[CandidateAssessment(candidate_id=pair["candidate"]["id"],
                verdict="invalid_rejection" if kind == "rejected" else "covered",
                reason="The source explicitly requests this export." if kind == "rejected" else "",
                suggested_fix="Accept the Excel export requirement." if kind == "rejected" else "") for pair in payload["pairs"]])
        result = Network(Config(self.input, self.output), SimpleNamespace(invoke=invoke)).audit_traceability(
            dict(documents=documents, candidates=[first, second], specification=specification, issues=[],
                 revision=2, source_audit_count=0))
        self.assertEqual(sorted(dispositions), ["accepted", "rejected"])
        self.assertTrue(any(issue.category == "blacklist" and issue.candidate_ids == [second.id] for issue in result["issues"]))

    def test_incremental_revision_preserves_an_unaffected_requirement(self):
        first = self.grounded()
        second = first.model_copy(update={"id": "CAND-00002", "statement": SECOND, "evidence_quote": SECOND})
        original = Requirement(name="CSV export", explanation=EXPLANATION, kind="functional", priority="P2",
            priority_reason="Source request.", candidate_ids=[first.id])
        untouched = original.model_copy(update={"name": "Excel export", "candidate_ids": [second.id]})
        spec = Specification(title="Test", scope="Test scope", glossary=[], blacklist=[], open_questions=[],
            requirements=[original, untouched])
        calls = []
        def invoke(*args):
            calls.append(args)
            self.assertIs(args[4], IncrementalPatch)
            self.assertTrue(args[3]["review_findings"])
            updated = IncrementalUpdate(**original.model_dump(exclude={"explanation"}), target_index=0,
                replacements=[TextReplacement(old_text="invented old fragment" if len(calls) == 1 else "requested representation",
                    new_text="selected output representation")],
                append_explanation="CSV export shall include all selected fields.")
            return IncrementalPatch(requirements=[updated], blacklist=[])
        result = Network(Config(self.input, self.output), SimpleNamespace(invoke=invoke)).refine(
            dict(revision=0, specification=spec, candidates=[first, second], issues=[Issue(category="description",
                severity="error", description="Preserve all selected CSV fields.", suggested_fix="Clarify CSV output.",
                candidate_ids=[first.id])]))
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["specification"].requirements[1], untouched)
        self.assertEqual(spec.requirements[0], original)
        self.assertIn("all selected fields", result["specification"].requirements[0].explanation)
        self.assertEqual(result["specification"].requirements[0].explanation,
            EXPLANATION.replace("requested representation", "selected output representation") + " CSV export shall include all selected fields.")

    def test_reviewer_can_recover_requirement_missed_by_extractor(self):
        state = self.execute(FakeClient(discover_missing=True))
        self.assertTrue(state["review_passed"])
        self.assertEqual(len(state["candidates"]), 2)
        self.assertEqual(state["revision"], 1)
        self.assertEqual({candidate.statement for candidate in state["candidates"]}, {SOURCE, SECOND})
        self.assertEqual([review["source_document_audits"] for review in state["history"]], [1, 0])

    def test_external_source_feedback_is_grounded_and_applied_once(self):
        feedback = self.root / "feedback.json"
        feedback.write_text(json.dumps(dict(apply_at_revision=0, additions=[dict(source_path="source.txt",
            candidate=text_candidate(SECOND).model_dump(), reason="The Excel request was missed.")])), encoding="utf-8")
        client = FakeClient()
        state = Network(Config(self.input, self.output, repair_batch_size=0, review_feedback=feedback), client).build().invoke({})
        self.assertTrue(state["review_passed"])
        self.assertTrue(state["external_feedback_applied"])
        self.assertEqual(state["revision"], 1)
        self.assertEqual(len(state["candidates"]), 2)
        self.assertEqual(state["candidates"][1].evidence_quote, SECOND)
        self.assertTrue((self.output / "external-review-feedback.json").is_file())

    def test_full_source_rescans_can_be_bounded_without_stopping_feedback(self):
        class TwoFailures(FakeClient):
            def invoke(inner_self, role, model, prompt, payload, schema, max_tokens=12000):
                if schema is ConsistencyAudit and inner_self.editor_calls <= 2:
                    return ConsistencyAudit(issues=[Issue(category="description", severity="error",
                        description="Synthetic detail needs correction.", suggested_fix="Correct the detail.",
                        candidate_ids=["CAND-00001"])])
                return super().invoke(role, model, prompt, payload, schema, max_tokens)
        client = TwoFailures()
        state = Network(Config(self.input, self.output, repair_batch_size=0, rescan_sources=True,
                               source_audit_rounds=2, max_revisions=3), client).build().invoke({})
        self.assertTrue(state["review_passed"])
        self.assertEqual(state["revision"], 2)
        self.assertEqual([review["source_document_audits"] for review in state["history"]], [1, 1, 0])
        self.assertEqual(client.audit_calls, 2)

    def test_parallel_audits_preserve_source_order_for_new_ids(self):
        (self.input / "another.txt").write_text(SOURCE + "\n" + SECOND, encoding="utf-8")

        class ParallelClient(FakeClient):
            def invoke(inner_self, role, model, prompt, payload, schema, max_tokens=12000):
                if schema is DocumentAudit:
                    if payload["document"]["id"] == "DOC-001":
                        time.sleep(0.03)  # Make the first source finish later.
                    found = any(item["statement"] == SECOND for item in payload["existing_source_candidates"])
                    return DocumentAudit(missing_candidates=[] if found else [text_candidate(SECOND)], issues=[])
                return super().invoke(role, model, prompt, payload, schema, max_tokens)

        state = self.execute(ParallelClient())
        self.assertTrue(state["review_passed"])
        self.assertEqual([(item.id, item.document_id) for item in state["candidates"][2:]],
                         [("CAND-00003", "DOC-001"), ("CAND-00004", "DOC-002")])

    def test_fabricated_evidence_is_rejected(self):
        documents, _ = load_corpus(self.input)
        with self.assertRaises(ValueError):
            ground_candidate(text_candidate("The system shall invent a feature."), documents[0], chunk_documents(documents)[0], "X")

    def test_grounding_records_source_line_numbers(self):
        documents, _ = load_corpus(self.input)
        candidate = ground_candidate(text_candidate(SECOND), documents[0], chunk_documents(documents)[0], "X")
        self.assertEqual((candidate.start_line, candidate.end_line), (2, 2))

    def test_grounding_repairs_only_presentation_and_saves_source_text(self):
        document = Document(id="D", path="source.txt", sha256="test", text="- Ability to export reports")
        item = text_candidate("ability to export reports.")
        candidate = ground_candidate(item, document, chunk_documents([document])[0], "X")
        self.assertEqual(candidate.evidence_quote, "Ability to export reports")
        wrapped = text_candidate('"ability to export reports."')
        self.assertEqual(ground_candidate(wrapped, document, chunk_documents([document])[0], "X").evidence_quote,
                         "Ability to export reports")
        with self.assertRaises(ValueError):
            ground_candidate(text_candidate("Ability to delete reports."), document, chunk_documents([document])[0], "X")

    def test_evidence_repair_preserves_all_original_candidate_statements(self):
        document = Document(id="D", path="source.txt", sha256="test",
                            text="Safety measures:\n- Audit trail for all purges\n- Separate confirmation step")
        bad = text_candidate("Safety measures: - Separate confirmation step")
        good = text_candidate("- Audit trail for all purges")
        repair_client = SimpleNamespace(invoke=lambda *args: QuoteRepairs(
            repairs=[QuoteRepair(candidate_index=0, evidence_quote="- Separate confirmation step")]))
        network = Network(Config(self.input, self.output), repair_client)
        grounded = network.grounded_candidates([bad, good], document, chunk_documents([document])[0], "gpt-4o-mini", "extract")
        self.assertEqual([item.statement for item in grounded], [bad.statement, good.statement])
        self.assertEqual(grounded[0].evidence_quote, "- Separate confirmation step")

    def test_chunking_does_not_drop_lines_and_makes_progress(self):
        document = Document(id="DOC-001", path="long.txt", sha256="test", text="\n".join(f"line {i}: " + "x" * 70 for i in range(100)))
        chunks = chunk_documents([document], max_chars=500, overlap_lines=8)
        covered = {line for chunk in chunks for line in range(chunk.start_line, chunk.end_line + 1)}
        self.assertEqual(covered, set(range(1, 101)))
        self.assertEqual(chunks[-1].end_line, 100)

    def test_nested_files_and_unsupported_formats_are_reported(self):
        nested = self.input / "conversations"
        nested.mkdir()
        (nested / "other.md").write_text("Another text.", encoding="utf-8")
        (self.input / "unreadable.pdf").write_bytes(b"not text")
        documents, skipped = load_corpus(self.input)
        self.assertEqual(len(documents), 2)
        self.assertIn("conversations/other.md", [document.path for document in documents])
        self.assertEqual(skipped, ["unreadable.pdf"])
        with self.assertRaises(ValueError):
            self.execute(FakeClient())

    def test_mime_email_preserves_embedded_conversation(self):
        message = EmailMessage()
        message["From"] = "sender@example.org"
        message["Subject"] = "Requirements discussion"
        message.set_content(SOURCE + "\n===\nFrom: reply@example.org\n" + SECOND)
        message.add_alternative("<p>HTML duplicate</p>", subtype="html")
        text = read_email(message.as_bytes())
        self.assertIn(SOURCE, text)
        self.assertIn(SECOND, text)
        self.assertNotIn("HTML duplicate", text)

    def test_validator_rejects_unknown_and_unaccounted_candidates(self):
        candidate = self.grounded()
        spec = Specification(title="Test", scope="Test scope", glossary=[], blacklist=[], open_questions=[],
            requirements=[Requirement(name="Export", explanation=EXPLANATION, kind="functional", priority="P2",
                                      priority_reason="Source request.", candidate_ids=["MADE-UP"])])
        categories = {issue.category for issue in validate_specification(spec, [candidate])}
        self.assertIn("provenance", categories)
        self.assertIn("completeness", categories)

    def test_three_distinct_permitted_models_are_enforced(self):
        with self.assertRaises(ValueError):
            Config(self.input, self.output, editor_model="gpt-4o-mini").validate()
        with self.assertRaises(ValueError):
            Config(self.input, self.output, editor_model="unapproved-model").validate()

    def test_empty_optional_endpoint_uses_official_api(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "unit-test-only", "OPENAI_BASE_URL": ""}):
            client = AgentClient(self.output)
            try:
                self.assertEqual(str(client.client.base_url), "https://api.openai.com/v1/")
            finally:
                client.close()

    def test_cache_reuses_only_identical_requests(self):
        response = SimpleNamespace(status="completed", output_parsed=CheckResult(ok=True), usage=None,
                                   model="test-served-model", id="synthetic-response")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "unit-test-only", "OPENAI_BASE_URL": ""}):
            client = AgentClient(self.output)
            try:
                with patch.object(client.client.responses, "parse", return_value=response) as call:
                    for prompt in ("same", "same", "changed"):
                        client.invoke("test", "gpt-4o-mini", prompt, {}, CheckResult)
                    self.assertEqual(call.call_count, 2)
                    self.assertEqual(client.events[1]["status"], "cache_hit")
            finally:
                client.close()


if __name__ == "__main__":
    unittest.main()
