"""Independently verify generated artifacts without making any model requests."""
import argparse
import json
import re
from pathlib import Path

from refinement.corpus import load_corpus, normalize
from refinement.llm import write_json
from refinement.schemas import Candidate, Specification
from refinement.validation import validate_specification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    errors = []
    documents, skipped = load_corpus(args.input)
    if skipped:
        errors.append("Unsupported input files are present.")
    sources = {doc.id: doc for doc in documents}
    manifest = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))["documents"]
    if {(doc.id, doc.path, doc.sha256) for doc in documents} != {(doc["id"], doc["path"], doc["sha256"]) for doc in manifest}:
        errors.append("Input corpus does not match the recorded source manifest.")
    candidates = [Candidate.model_validate(item) for item in json.loads((output / "candidates.json").read_text(encoding="utf-8"))]
    if len({item.id for item in candidates}) != len(candidates):
        errors.append("Candidate IDs are not unique.")
    for candidate in candidates:
        document = sources.get(candidate.document_id)
        if document is None:
            errors.append(f"Unknown source for {candidate.id}.")
            continue
        saved = (output / "sources" / f"{document.id}.txt").read_text(encoding="utf-8")
        if saved != document.text:
            errors.append(f"Normalized source copy differs: {document.id}.")
        lines = document.text.splitlines()
        if not 1 <= candidate.start_line <= candidate.end_line <= len(lines):
            errors.append(f"Invalid line range: {candidate.id}.")
        excerpt = normalize("\n".join(lines[candidate.start_line - 1:candidate.end_line]))
        if candidate.evidence_quote not in excerpt:
            errors.append(f"Stored literal evidence is absent from its source lines: {candidate.id}.")
    raw = json.loads((output / "requirements.json").read_text(encoding="utf-8"))
    spec_data = {key: value for key, value in raw.items() if key != "review_passed"}
    identifiers = []
    for key in ("requirements", "blacklist"):
        for item in spec_data[key]:
            identifiers.append(item["id"])
            item.pop("id")
    specification = Specification.model_validate(spec_data)
    errors.extend(issue.description for issue in validate_specification(specification, candidates))
    if len(identifiers) != len(set(identifiers)):
        errors.append("Final requirement / blacklist IDs are not unique.")
    if any(not re.fullmatch(r"(?:REQ|BL)-\d{4,}", identifier) for identifier in identifiers):
        errors.append("Unexpected final ID format.")
    markdown = (output / "requirements.md").read_text(encoding="utf-8")
    if any(identifier not in markdown for identifier in identifiers):
        errors.append("Markdown is missing an exported requirement ID.")
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    assessments = json.loads((output / f"traceability-{metrics['revisions']:02d}.json").read_text(encoding="utf-8"))
    assessed_ids = [item["candidate_id"] for item in assessments]
    if set(assessed_ids) != {item.id for item in candidates} or len(assessed_ids) != len(candidates):
        errors.append("Final semantic traceability audit did not assess every candidate exactly once.")
    if any(item["verdict"] != "covered" for item in assessments):
        errors.append("Final semantic traceability audit retains unresolved findings.")
    trace = [json.loads(line) for line in (output / "run_trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    completed = [event for event in trace if event.get("status") == "completed"]
    served_models = sorted({event["served_model"] for event in completed})
    roles = {event["role"] for event in completed}
    if len(served_models) < 3 or not {"extract", "refine", "review_source", "review_global", "review_traceability"}.issubset(roles):
        errors.append("Trace does not demonstrate the three actual model-backed roles.")
    result = dict(structural_checks_passed=not errors, automatic_review_passed=raw["review_passed"],
                  source_count=len(documents), grounded_candidate_count=len(candidates), final_identifier_count=len(identifiers),
                  semantic_bindings_assessed=len(assessments),
                  served_models=served_models, completed_api_calls_in_trace=len(completed), errors=errors,
                  interpretation="Structural verification and review status do not prove perfect semantic completeness.")
    write_json(output / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors and raw["review_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
