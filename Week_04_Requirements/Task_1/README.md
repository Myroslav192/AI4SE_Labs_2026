# Software Requirements Refinement Network

Python + LangGraph implementation for Task 1. It recursively reads a directory of
texts, extracts source-grounded requirement candidates with one OpenAI model,
reconciles them with a second, and independently audits coverage and consistency
with a third. A separate semantic traceability agent checks every source-to-requirement
association. A bounded feedback loop sends findings back to the editor.

## Deliverables

- `run.py` and `refinement/`: executable network and visible agent prompts.
- `REPORT.md`: architecture, design choices, assignment compliance and limitations.
- `WALKTHROUGH_UK.md`: detailed Ukrainian explanation for studying and presenting the work.
- `artifacts/corpus_run/requirements.md`: the authoritative generated requirements document after the actual run.
- `artifacts/corpus_run/requirements.json`: machine-readable version of the same specification.
- `artifacts/corpus_run/metrics.json`, `review_history.json`, `run_trace.jsonl`: execution evidence.
- `artifacts/corpus_run/coverage-patches-xx.json`: explicit small-batch decisions for omitted or multiply assigned candidate IDs.
- `artifacts/corpus_run/traceability-xx.json`: exhaustive semantic decisions on candidate/evidence/requirement associations.
- `artifacts/corpus_run/candidate-corrections-xx.json`: grounded interpretation/evidence corrections with before/after history.
- `artifacts/corpus_run/review-decisions-xx.json`: raw review findings and the reason for retaining or dismissing each.
- `artifacts/semantic_regression/result.json`: real API regression for the previously observed erroneous evidence association.
- `tests/test_network.py`: offline tests of the compiled graph and deterministic behavior.

The generated requirements file is produced by the network; it is not a manually
written sample or the output of an offline test double. Its status states whether
automatic review passed or unresolved errors remain.

## Setup

Use Python **3.10 or newer**; Python 3.12 is a suitable choice. Run the commands
from this project directory. A virtual environment keeps its dependencies separate.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
```

Set the teacher-provided key in `.env`:

```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=
```

Leave `OPENAI_BASE_URL` blank for the official OpenAI endpoint. Set it only if the
teacher supplied a gateway URL. `.env` is excluded from version control and the
submission archive. Do not put the key in Python source, screenshots or reports.
The loader also accepts a key already set in the environment; existing environment
variables take precedence over `.env`.

If the exact dependency lock cannot be installed on a different supported Python
version, install the direct constraints in `requirements.txt` instead. The lock
records the environment used for the submitted validation.

## Commands

Inventory the input without making API calls:

```powershell
.\.venv\Scripts\python.exe run.py inspect --input data\corpus
```

Check key, model access and Structured Outputs with three small API requests:

```powershell
.\.venv\Scripts\python.exe run.py check-api
```

Execute the actual network on the supplied corpus:

```powershell
.\.venv\Scripts\python.exe run.py run --input data\corpus --output artifacts\corpus_run --max-revisions 5 --max-calls 220 --review-workers 4 --rescan-sources --source-audit-rounds 2 --feedback review_feedback.json
```

The submitted command includes `--feedback review_feedback.json` to reproduce the
source-grounded coding-agent review inputs used during finalization. This optional
JSON supplies literal quotations and additional candidates; the same graph must
reconcile and audit them. It applies once at the specified revision. For another
corpus omit this option or supply an appropriate review file. No final requirement
paragraph is manually substituted by this mechanism.

Use the same command with any other input directory. No input filenames, PINES
requirement IDs, feature lists or expected requirement counts are encoded in the
implementation. Supported file formats are UTF-8/Windows-1252 `.txt`, `.md`, and
plain-text `.eml` including MIME multipart messages with a text body. Subdirectories
are included. Unsupported formats cause a visible error on a full run rather than
being silently omitted; convert them to text first. PDF and Word parsing are not
part of this implementation.

Output defaults to English, matching the corpus. To change the language, add
`--language Ukrainian`. The narrative requirement content is requested in that
language; the deterministic document headings and priority legend remain English.

Select any three different models from the assignment's permitted list:

```powershell
.\.venv\Scripts\python.exe run.py run --input data\corpus --extractor-model gpt-4o-mini --editor-model gpt-5-mini --reviewer-model gpt-5-nano
```

The default API is Responses with Structured Outputs. For an instructor gateway
that supports only Chat Completions, add `--api-mode chat`. Availability still
depends on the credentials and gateway; unavailable models produce an error and
are never silently substituted.

Save the compiled graph diagram without API calls:

```powershell
.\.venv\Scripts\python.exe run.py graph
```

Run offline tests without a valid API key:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Independently check the generated IDs, original hashes, literal evidence, candidate
disposition and real model trace without making API calls:

```powershell
.\.venv\Scripts\python.exe verify.py --input data\corpus --output artifacts\corpus_run
```

Exit status: `0` = successful operation / automatic review passed; `1` = execution
error; `2` = generated draft still has review errors, or inventory found unsupported
files. Open questions and disclosed warnings can remain in a reviewed specification.

## Resuming and cost control

Every successful LLM response is cached under the output directory. The key covers
the exact model, endpoint, API mode, prompt, payload, output schema and token limit.
Rerun with the same inputs and output folder after an interruption to reuse those
responses. Changing inputs, prompts or models invalidates the relevant cache entries.
This is response caching, not a durable LangGraph checkpoint service.

After the first complete draft, revisions normally use targeted editor patches
for candidate-referenced errors and newly found candidates. This preserves
unaffected paragraphs. Findings without candidate references fall back to a full
regeneration. The same graph feedback edge and complete output schema apply.

`--max-revisions` bounds editor/reviewer repetitions, and `--max-calls` bounds SDK
invocations (default 150). The SDK may retry transient failures up to twice, so the
invocation cap is not a strict monetary or HTTP-request budget. Actual token usage
for successful new calls is recorded in `metrics.json`; cache hits incur no new
model call. There is no promise of byte-identical results on fresh uncached runs.

Source-document audits use four worker threads and are collected in stable input
order. Use `--review-workers 1` to make those requests sequential for an account
with tighter rate limits. Editing, global review and feedback routing remain
sequential.

Every original document receives an independent coverage audit in the first
review round. Subsequent rounds review the revised specification and complete
grounded candidate ledger. Add `--rescan-sources` to repeat the full-document audits
after every revision; this increases requests and may discover further candidates.
The submitted run uses two full-source rounds with `--source-audit-rounds 2`:
the baseline and one rescan after revision. Subsequent rounds stabilize the
grounded candidate ledger and retain exhaustive semantic association and global
quality checks. Omit the cap to rescan after every revision. Source audits and exhaustive traceability
audits use `gpt-5-mini`; the global cross-requirement review uses `gpt-5-nano`.
Traceability review returns an explicit decision for each assigned candidate,
including whether its evidence really supports its interpretation. A matching
quotation alone cannot establish that relationship.

The trace contains model names, response IDs, hashes, timings and token counts.
Source evidence and outputs are saved separately. Credential values are never
logged. Source files and generated evidence should be shared only as appropriate
for the input corpus.
