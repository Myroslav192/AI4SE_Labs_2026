# Week 06: Repository-aware RAG coding submission

The submitted repository is already solved. Ten implementations were generated
through the pipeline in 14 real API calls; the final repository passed 481 tests.
Checking this submission does not require a generative API call.

## Deliverables

| Task | Implementation/data | Report/evidence |
| --- | --- | --- |
| 1: Clone | [Solved source](solution/AI4SE_Playground/), ordinary files | [Cloning report](solution/reports/task1_cloning.md) |
| 2: Chunking | [Chunker](solution/rag/chunk_repository.py), [55 chunks](solution/artifacts/chunks.jsonl), [manifest](solution/artifacts/chunks.manifest.json) | [Chunking report](solution/reports/task2_chunking.md), [checks](solution/artifacts/task2_verification.json) |
| 3: Embeddings | [Embedding script](solution/rag/embed_repository.py), [shared encoder](solution/rag/local_embeddings.py), [NPZ](solution/artifacts/embeddings.npz), [metadata](solution/artifacts/embeddings.metadata.json) | [Embedding report](solution/reports/task3_embeddings.md) |
| 4: Retrieval | [Retriever/query builder](solution/rag/retrieve_chunks.py), [evaluation script](solution/rag/evaluate_retrieval.py), [actual evaluation](solution/artifacts/retrieval_evaluation.json) | [Retrieval report](solution/reports/task4_retrieval.md) |
| 5: Generation | [Solver](solution/rag/solve_tasks.py), [scoped editor](solution/rag/method_editing.py), [actual run summary](solution/artifacts/task5_runs/run-e1ba175ad737/summary.json), [patch](solution/artifacts/generated_changes.patch) | [Generation report](solution/reports/task5_generation_and_tests.md), [final tests](solution/artifacts/final_tests.log), [audit](solution/artifacts/task5_final_verification.json) |
| 6: Bonus | Design only; no second implementation | [Bonus design](solution/reports/task6_bonus_design.md) |
| Packaging | [SHA-256 manifest](SHA256SUMS), [verification tool](solution/tools/verify_submission.py) | [Package verification](solution/reports/package_verification.md) |

[Assignments](Assignments/) contains byte-for-byte copies of the five mandatory
assignments, bonus, and [missing_code.json](Assignments/missing_code.json).
The supplied workspace originally stored these outside this directory; the copies
were made for submission without changing the originals. All historical reports,
attempts, rejections, and logs are retained unchanged. Their recorded absolute
paths and older `../missing_code.json` commands describe the original execution
layout; use the commands here for the extracted package.

Original repository: https://github.com/Neltharion59/AI4SE_Playground

Pinned original commit: `b17f75374a6d63f0f245e472bb707e658c1b3cf7`.
The ZIP deliberately omits Git metadata; the live working clone retains its `.git`.

## Check the submitted solved repository

Start in the extracted submission root. Python 3.12 was used (3.12.16 on Linux
x86_64); the RAG scripts require Python 3.10+. The repository's unit tests use
only the standard library:

```bash
python3 -m venv .venv
(
  cd solution/AI4SE_Playground/playground
  ../../../.venv/bin/python -m unittest discover -s tests -v
)
sha256sum -c SHA256SUMS
```

The archived `.venv`, caches, credentials, and model weights are intentionally
absent. For full artifact checks and CLI use, install the tested stack:

```bash
.venv/bin/python -m pip install -r solution/requirements-task5.lock.txt
.venv/bin/python -m pip check
.venv/bin/python solution/tools/verify_submission.py --root .
.venv/bin/python solution/rag/solve_tasks.py --help
.venv/bin/python -m unittest discover -s solution/rag/tests -p test_solving.py -v
```

The full lock includes CPU PyTorch, NumPy, Sentence Transformers, OpenAI SDK, and
dotenv. The task-specific requirements files remain available. A fresh dependency
installation was **not** tested during packaging: verification reused the existing
environment and cached model. Other platforms may need different wheel selections.
The verifier itself needs NumPy; it does not call a generative model or download weights.

To use local retrieval with the submitted frozen vectors, first download the
exact recorded encoder into a local cache if not already available:

```bash
.venv/bin/python - <<'PY'
import sys
sys.path.insert(0, "solution/rag")
from local_embeddings import TextEncoder
TextEncoder.from_metadata("solution/artifacts/embeddings.metadata.json",
    cache_dir=".cache/huggingface", local_files_only=False)
PY
HF_HUB_OFFLINE=1 .venv/bin/python solution/rag/retrieve_chunks.py 'Return the number of line items in an order.' --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface -n 5
```

Encoder revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` of
`sentence-transformers/all-MiniLM-L6-v2`. This downloads public model files only.
Retrieval uses exact cosine search over 55 normalized 384-dimensional vectors.

## Frozen evidence versus solved source

The chunks, source manifest, embeddings, and retrieval evaluation represent the
**original pinned source with ten stubs**. The submitted source contains the later
generated implementations. Do not rebuild the index from the solved repository
and describe it as the same experiment. Old source ranges and hashes refer to the
frozen version, not the current edited files.

`verify_submission.py` reconstructs original source from the chunks for hash/span
checks and compares final method bodies with accepted API responses. It does not
need `.git`. The historical `verify_chunking.py` and source-span retrieval checks
expect the original clean Git checkout; they are not checks of the solved tree.
Older RAG integration tests also assume the original workspace/cache layout; use
the package verifier and commands above for this packaged solved version.

Observed results: 55 chunks; top-five target-method coverage 10/10 (a diagnostic,
not a completeness guarantee); 10 accepted implementations from 14 API calls,
including four retained validation rejections. The baseline was **481 tests,
35 failures, 17 errors, exit 1**; the final result was **481 tests, 0 failures,
0 errors, exit 0**. Passing existing tests does not prove unseen-case correctness.

## Reproduce the full experiment separately

These commands are a reproduction recipe, not additional executions performed
during packaging. Work in a new directory so historical evidence and the solved
submission are not overwritten. Start from the original pinned commit:

```bash
mkdir reproduction
cp -R Assignments reproduction/
mkdir -p reproduction/solution
cp -R solution/rag reproduction/solution/
cp solution/requirements-task5.lock.txt reproduction/solution/
cp .env.example .gitignore reproduction/
cd reproduction
python3 -m venv .venv
.venv/bin/python -m pip install -r solution/requirements-task5.lock.txt
git clone https://github.com/Neltharion59/AI4SE_Playground solution/AI4SE_Playground
git -C solution/AI4SE_Playground checkout --detach b17f75374a6d63f0f245e472bb707e658c1b3cf7
mkdir -p solution/artifacts
(
  cd solution/AI4SE_Playground/playground
  ../../../.venv/bin/python -m unittest discover -s tests -v
) > solution/artifacts/baseline_tests.log 2>&1
.venv/bin/python solution/rag/chunk_repository.py solution/AI4SE_Playground solution/artifacts/chunks.jsonl
.venv/bin/python solution/rag/verify_chunking.py solution/AI4SE_Playground solution/artifacts/chunks.jsonl Assignments/missing_code.json
.venv/bin/python solution/rag/embed_repository.py solution/artifacts/chunks.jsonl solution/artifacts/embeddings.npz --cache-dir .cache/huggingface --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41
HF_HUB_OFFLINE=1 .venv/bin/python solution/rag/retrieve_chunks.py 'Return the number of line items in an order.' --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface -n 5
HF_HUB_OFFLINE=1 .venv/bin/python solution/rag/evaluate_retrieval.py --tasks Assignments/missing_code.json --repository solution/AI4SE_Playground --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface --output solution/artifacts/retrieval_evaluation.json
```

The baseline test command is expected to exit 1 for the original stubbed source.
Token windows/normalization are recorded in metadata; floating-point embeddings
and new model outputs need not be byte-identical across environments or runs.

### Optional real generation in the reproduction directory

This step makes paid model calls and is unnecessary for checking the submission.
Copy `.env.example` to `.env` and configure `OPENAI_API_KEY` locally. Do not put
credentials in a command, chat, or artifact. `OPENAI_MODEL` defaults to
`gpt-5-mini`; the original exact model allowlist is enforced. Optional
`OPENAI_BASE_URL` must be Responses-compatible, normally including `/v1`.
Environment variables take precedence. Loading `.env` is explicit:

```bash
cp .env.example .env
# Edit .env locally before running the next command.
HF_HUB_OFFLINE=1 .venv/bin/python solution/rag/solve_tasks.py --tasks Assignments/missing_code.json --repository solution/AI4SE_Playground --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface --env-file .env
```

The solver creates new run evidence, writes only validated target bodies, and
automatically runs the same full repository tests. Retain the original index
through generation. Bounded feedback/regeneration and API configuration details
are documented in [Task 5 usage](solution/rag/TASK5_USAGE.md).
