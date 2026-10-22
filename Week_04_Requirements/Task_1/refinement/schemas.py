"""Typed contracts shared by the network's LLM agents and deterministic nodes."""
from typing import Literal

from pydantic import BaseModel, ConfigDict

Kind = Literal["functional", "nonfunctional", "constraint", "assumption", "dependency"]
Priority = Literal["P1", "P2", "P3"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Document(StrictModel):
    id: str
    path: str
    sha256: str
    text: str


class Chunk(StrictModel):
    id: str
    document_id: str
    start_line: int
    end_line: int
    text: str


class CandidateText(StrictModel):
    name: str
    statement: str
    kind: Kind
    priority_hint: Literal["high", "medium", "low", "unspecified"]
    evidence_quote: str


class Extraction(StrictModel):
    candidates: list[CandidateText]
    ignored_content_summary: str


class QuoteRepair(StrictModel):
    candidate_index: int
    evidence_quote: str


class QuoteRepairs(StrictModel):
    repairs: list[QuoteRepair]


class Candidate(CandidateText):
    id: str
    document_id: str
    chunk_id: str
    start_line: int
    end_line: int


class Term(StrictModel):
    term: str
    definition: str


class Requirement(StrictModel):
    name: str
    explanation: str
    kind: Kind
    priority: Priority
    priority_reason: str
    candidate_ids: list[str]


class RejectedRequirement(StrictModel):
    name: str
    statement: str
    category: Literal["conflicting", "nonsensical", "out_of_scope"]
    reason: str
    candidate_ids: list[str]


class OpenQuestion(StrictModel):
    question: str
    reason: str
    candidate_ids: list[str]


class Specification(StrictModel):
    title: str
    scope: str
    glossary: list[Term]
    requirements: list[Requirement]
    blacklist: list[RejectedRequirement]
    open_questions: list[OpenQuestion]


class RequirementUpdate(Requirement):
    target_index: int


class CoveragePatch(StrictModel):
    requirements: list[RequirementUpdate]
    blacklist: list[RejectedRequirement]


class TextReplacement(StrictModel):
    old_text: str
    new_text: str


class IncrementalUpdate(StrictModel):
    target_index: int
    name: str
    kind: Kind
    priority: Priority
    priority_reason: str
    candidate_ids: list[str]
    replacements: list[TextReplacement]
    append_explanation: str


class IncrementalPatch(StrictModel):
    requirements: list[IncrementalUpdate]
    blacklist: list[RejectedRequirement]


class Issue(StrictModel):
    category: Literal["completeness", "duplicate", "conflict", "terminology", "provenance", "priority", "description", "blacklist", "structure"]
    severity: Literal["error", "warning"]
    description: str
    suggested_fix: str
    candidate_ids: list[str]


class DocumentAudit(StrictModel):
    missing_candidates: list[CandidateText]
    issues: list[Issue]


class ConsistencyAudit(StrictModel):
    issues: list[Issue]


class CandidateAssessment(StrictModel):
    candidate_id: str
    verdict: Literal["covered", "missing_detail", "wrong_requirement", "unsupported", "invalid_rejection"]
    reason: str
    suggested_fix: str


class TraceabilityAudit(StrictModel):
    assessments: list[CandidateAssessment]


class IssueDecision(StrictModel):
    issue_index: int
    retain: bool
    reason: str


class ReviewAdjudication(StrictModel):
    decisions: list[IssueDecision]


class FeedbackAddition(StrictModel):
    source_path: str
    candidate: CandidateText
    reason: str


class ReviewFeedback(StrictModel):
    apply_at_revision: int
    additions: list[FeedbackAddition]


class CandidateCorrection(CandidateText):
    candidate_id: str
    reason: str


class InterpretationRepairs(StrictModel):
    corrections: list[CandidateCorrection]


class CheckResult(StrictModel):
    ok: bool
