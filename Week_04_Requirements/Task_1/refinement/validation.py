"""Checks that do not need or trust an LLM."""
import re
from collections import Counter

from .schemas import Candidate, Issue, Specification


def validate_specification(spec: Specification, candidates: list[Candidate]) -> list[Issue]:
    issues = []

    def add(category, description, ids=None):
        issues.append(Issue(category=category, severity="error", description=description,
                            suggested_fix="Correct this issue in the next complete specification.", candidate_ids=ids or []))

    known = {candidate.id for candidate in candidates}
    occurrences = Counter()
    if not spec.title.strip() or not spec.scope.strip() or not spec.requirements:
        add("structure", "Title, scope and at least one accepted requirement are required.")
    seen_text = set()
    for entry in [*spec.requirements, *spec.blacklist]:
        if not entry.name.strip() or not entry.candidate_ids:
            add("provenance", "Each accepted or rejected requirement needs a name and source candidate IDs.")
        for candidate_id in entry.candidate_ids:
            occurrences[candidate_id] += 1
            if candidate_id not in known:
                add("provenance", f"Unknown candidate ID: {candidate_id}", [candidate_id])
    for candidate_id in sorted(known):
        if occurrences[candidate_id] == 0:
            add("completeness", f"Candidate {candidate_id} has no accepted or rejected disposition.", [candidate_id])
        elif occurrences[candidate_id] > 1:
            add("duplicate", f"Candidate {candidate_id} occurs in multiple dispositions; merge or reassign.", [candidate_id])
    for requirement in spec.requirements:
        text_key = " ".join(re.findall(r"\w+", requirement.explanation.casefold()))
        if text_key in seen_text:
            add("duplicate", f"Exact duplicate requirement text: {requirement.name}", requirement.candidate_ids)
        seen_text.add(text_key)
        if len(requirement.explanation.split()) < 25 or "\n\n" in requirement.explanation.strip():
            add("description", f"Requirement needs one substantive paragraph: {requirement.name}", requirement.candidate_ids)
        if not requirement.priority_reason.strip():
            add("priority", f"Missing priority justification: {requirement.name}", requirement.candidate_ids)
    for entry in spec.blacklist:
        if len(entry.reason.split()) < 6 or not entry.statement.strip():
            add("blacklist", f"Rejection needs the original proposal and a specific reason: {entry.name}", entry.candidate_ids)
    for question in spec.open_questions:
        for candidate_id in question.candidate_ids:
            if candidate_id not in known:
                add("provenance", f"Open question refers to unknown candidate {candidate_id}.", [candidate_id])
    terms = [term.term.strip().casefold() for term in spec.glossary]
    if len(terms) != len(set(terms)):
        add("terminology", "Glossary contains duplicate terms.")
    return issues
