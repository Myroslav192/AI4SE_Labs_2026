# Task 5 configuration and execution

Run commands from `Week_06_Implementation`. Use the existing project `.venv`.

## Dependencies

```bash
.venv/bin/python -m pip install -r solution/requirements-task5.lock.txt
.venv/bin/python -m pip check
```

The lock includes the existing CPU embedding stack plus tested `openai==2.8.1`
and `python-dotenv==1.2.1`. The smaller `requirements-task5.txt` installs just
the additions when Task 3 dependencies are already installed.

## Credentials

```bash
cp .env.example .env
```

Edit the project-root `.env` locally and fill in `OPENAI_API_KEY`. Do not put
the key in the command line, chat, reports, or artifacts. The project `.gitignore`
ignores `.env` and `.env.*`, except the credential-free `.env.example`.
The pipeline loads an env file only when explicitly passed with `--env-file`.
It never searches other directories/weeks for credentials. Existing process
environment variables take precedence over `.env`. A variable exported in a
different terminal may not be inherited by the execution tool; the explicit
project-local file is the most direct configuration method here.

`OPENAI_MODEL` defaults to `gpt-5-mini`. Only exact model names from the Task 5
allowlist are accepted. An optional instructor-provided `OPENAI_BASE_URL` must
point to an OpenAI **Responses-compatible** API base (usually ending in `/v1`).
Do not put authentication in the URL. No alternative endpoint/model is silently
selected. API account access, model permission, quota, and connectivity can be
confirmed only by actual requests.

## Batch execution

The supplied workspace has no `Assignments/missing_code.json`; the unchanged
original manifest is `../missing_code.json`. `--tasks` accepts either location.

```bash
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python solution/rag/solve_tasks.py --tasks ../missing_code.json --repository solution/AI4SE_Playground --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface --env-file .env
```

`HF_HUB_OFFLINE=1` applies only to the local embedding model's Hugging Face
loader; it does not disable the OpenAI SDK's HTTPS requests. If credentials are
absent, omit `--env-file` to prepare actual retrieval/prompts and receive an
explicit blocked result. A missing explicit env file is a configuration error.
Prepared prompts are not generation evidence or a completed Task 5.

The SDK request uses `model`, `instructions`, `input`, `max_output_tokens=4096`,
and `store=False`. Sampling/reasoning overrides are omitted. Output allowance
includes reasoning tokens; incomplete responses are rejected, not applied.
SDK internal retries are disabled. `--transport-retries` defaults to 2, so at
most three transport requests occur per generation attempt, with bounded
backoff. `--max-regenerations` defaults to 2, so at most three generations occur
per task. Each counter is independently bounded to 0..2. Requests use a 90-second
SDK timeout. These are upper bounds, not measured usage or cost.

Every invocation creates a new `solution/artifacts/task5_runs/run-*` directory.
Each task stores its actual query, five ranked original chunks, complete prompt,
and status. Real attempts additionally store the returned code, model/usage
metadata when returned, separate transport records, validation result, recoverable
original source, and applied diff. Previous runs/attempts are retained.
No mock-generation mode exists in the CLI.

After applied changes, the CLI runs the baseline's exact test invocation from
the clone's `playground` directory: `python -m unittest discover -s tests -v`.
The actual interpreter, result, counts, baseline comparison, and failing test
names are recorded in `final_tests.status.json`. Complete output is saved in
`final_tests.log` and copied into the run directory. A 120-second test timeout
is reported explicitly. Credentials are removed from the test process environment.
If no code was applied, `final_tests.log` contains a **NOT RUN** marker and no
invented test result. `generated_changes.patch` reflects the actual Git diff.

## Reusable solver and corrections

```python
from solve_tasks import solve_task

result = solve_task(textual_task, target_metadata, repository=repo,
                    retriever=existing_retriever, client=configured_openai_client,
                    evidence_directory=new_task_evidence_directory)
```

Target metadata supplies `file`, `class`, and `method` separately from the
behavior description. Each task retrieves once through Task 4's shared query
builder and always sends exactly five unchanged chunks. Validation-driven
regenerations reuse those same five chunks and receive explicit rejection
feedback. No source is reindexed.

Inspect actual remaining test failures before requesting corrections. To correct
an already implemented method, provide a JSON feedback file mapping
`Class.method` to an English explanation of observed failures, then rerun with
`--only Class.method --feedback-file path/to/feedback.json` and the same artifact
arguments. Do not include manually authored replacement code. An existing
implementation is skipped unless explicit feedback is provided. New runs retain
earlier attempts and reuse the frozen index/query builder. Reaching the attempt
limit leaves a reported unresolved failure; tests/unrelated source must not be
edited to make the run pass.

AST/signature/docstring checks, compilation, byte-preserving body splicing, backups,
and atomic replacement restrict editing. Returned text is never executed to patch
files. Structural validation cannot prove functional correctness; the actual
repository tests are still required. Inline one-line method bodies are explicitly
unsupported by the editor; this does not affect the ten supplied targets.

## Offline verification

```bash
HF_HUB_OFFLINE=1 .venv/bin/python -m unittest discover -s solution/rag/tests -p test_solving.py -v
```

These tests use unrelated toy methods and explicitly mocked SDK HTTP transport
in temporary directories. They make no live generation requests and supply no
implementations for the ten assignment methods. Actual Task 4 retrieval is also
checked by the prepared batch evidence against `retrieval_evaluation.json`.

Official references: [Responses create parameters](https://developers.openai.com/api/reference/python/resources/responses/methods/create),
[GPT-5 mini](https://developers.openai.com/api/docs/models/gpt-5-mini).
