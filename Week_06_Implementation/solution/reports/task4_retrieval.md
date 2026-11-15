# Task 4: Exact embedding retrieval

## Method and interface

Task 4, the existing embedding implementation, and Task 2/3 artifacts were inspected first. `retrieve_chunks.py` provides the reusable `retrieve_chunks(task, n, *, chunks_path, embeddings_path, metadata_path, ...)` function, reusable `ChunkRetriever.search(task, n)`, and a JSON CLI. Reusing a retriever avoids reloading the encoder for each query. Artifact/cache locations are arguments; no machine-specific paths are embedded.

The corpus is the existing **55 × 384** float32 matrix. The query uses Task 3's `TextEncoder.from_metadata`, pinned to model revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, on CPU and offline. Plain query text receives the same token-window handling: 256-token effective limit, two special tokens, 254 payload tokens, 32-token overlap, payload-weighted aggregation, and L2 normalization. Long queries are not silently truncated.

The query is normalized again in float64. Each score is the float64 dot product of a stored unit vector and the normalized query: cosine similarity, within the stored vectors' float32 normalization tolerance. All rows are scored, then sorted by descending score and ascending chunk ID for exact ties. There is no score rounding, file boost, target-specific branch, manual insertion, or context expansion.

Exact NumPy search is appropriate for 55 rows: 21,120 vector-coordinate products per query and a small full sort, without approximate-search machinery or a database. It returns `min(n, 55)` distinct chunks, with rank, ID, score, path, inclusive line range, symbols, enclosing classes, context-reference IDs, and unchanged original source text. `n` must be a positive integer; booleans, floats, strings in the Python API, zero, and negative values are rejected. Empty queries are also rejected.

## Artifact validation

Before search, the loader checks schema/model compatibility, resolved revision format, dimensions, input representation, aggregation/normalization, storage layout, source-manifest hash, source provenance and commit, chunks-file hash, NPZ hash/integrity, matching unique IDs and row order, matrix dtype/shape, finite unit vectors, and each row's embedding-text hash. NumPy loading uses `allow_pickle=False`. The loaded encoder's full settings and tokenizer must match metadata. Missing, corrupt, or incompatible artifacts produce `ArtifactError`; the CLI reports a clear error and exits nonzero. Existing shared helpers required no modification.

## Query construction and actual evaluation

`build_task_query` is the shared builder for Task 5. It uses the supplied file, class, method, and description (`docstring` in the current manifest), removing only surrounding whitespace/triple-quote delimiters:

```text
Implement {class}.{method} in {file}.
Required behavior: {description}
```

The fixed template was applied to all 10 original tasks with `n=5`. Queries contained 28–44 payload tokens and each fit one model window. `evaluate_retrieval.py` saves the actual query, query-window details, all five ranked results including scores/source text, original target span, and hit outcome in `retrieval_evaluation.json`. AST target spans include decorators and are checked against the indexed source hashes. These spans are inspected after ranking and never influence it.

| Target method | Target chunk rank | Score |
| --- | ---: | ---: |
| `OrderStatus.is_terminal` | 2 | 0.520572 |
| `InventoryLedger.__contains__` | 1 | 0.669923 |
| `Warehouse.stock_report` | 1 | 0.627347 |
| `OrderStateMachine.transition` | 1 | 0.686446 |
| `OrderLog.by_status` | 3 | 0.533210 |
| `Customer.can_afford` | 2 | 0.597794 |
| `Order.__len__` | 1 | 0.611805 |
| `BulkDiscountPricing.price` | 1 | 0.723563 |
| `EventBus.__contains__` | 1 | 0.679078 |
| `Money.__bool__` | 1 | 0.711073 |

Result: **10/10 target-method hits in the top five, zero misses**. A hit requires one returned chunk to contain the complete original method span in the correct source file. The query template, tasks, and scores were not adjusted after observing results. JSON stores unrounded scores; the table rounds for readability.

## Commands and verification

Executed from `Week_06_Implementation` using the existing environment and dependencies:

```bash
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python solution/rag/retrieve_chunks.py 'Return the number of line items in an order.' --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface -n 5 > solution/artifacts/task4_cli_example.json
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python solution/rag/evaluate_retrieval.py --tasks ../missing_code.json --repository solution/AI4SE_Playground --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface --output solution/artifacts/retrieval_evaluation.json
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python -m unittest discover -s solution/rag/tests -p test_retrieval.py -v > solution/artifacts/task4_tests.log 2>&1
```

The CLI, evaluation, and final test run exited **0**. A separate CLI invocation with `-n 0` exited **2**, reporting that `n` must be a positive integer.

All **9 tests passed**. An independent scalar example used query `(3,4)` and rows `b=(1,0), a=(1,0), c=(0,1), d=(-1,0)`: scores `0.6, 0.6, 0.8, -0.6`, giving `c,a,b,d`, including the ID tie-breaker after row permutation. Tests also checked actual-corpus scores against Python scalar arithmetic, saved CLI results, deterministic repeated search, distinct results, `n=100` returning all 55 rows, invalid inputs, complete long-query windows, corrupt/mismatched artifacts, and saved evaluation queries and target spans.

`task4_verification.json` records checks and preservation hashes. All **28 pre-existing deliverable/assignment files** remain byte-unchanged, all indexed source hashes match Task 2, all 10 methods remain `pass`, and the nested Git repository remains clean and intact. No embeddings were rebuilt, no repository tests were changed or rerun, and the baseline log is unchanged. No generative LLM was called.

Target-method coverage is only a **diagnostic proxy**. It does not prove retrieval of every required dependency, test, invariant, or other context, and does not establish that generated code will be correct. This small evaluation uses explicit target names and paths; it does not demonstrate optimal retrieval quality or performance on vague queries. Task 4 has no remaining blocker.
