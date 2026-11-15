# Task 5: RAG generation and repository tests

## Outcome

**All ten missing methods received real model-generated implementations. The full repository suite passed: 481 tests, zero failures, zero errors, exit code 0.** The IDE assistant authored the pipeline and unrelated toy test fixtures, not the ten production implementations. Every applied method body matches an actual accepted model response.

The completed generation run is `solution/artifacts/task5_runs/run-e1ba175ad737`. It contains **14 real API responses**, ten accepted implementations and four rejected responses. No transport retries were needed. An earlier credential-free preparation run, `run-e97ee01a17df`, remains preserved and is explicitly marked blocked with zero API calls; it is not counted as generation.

## Configuration and pipeline

The original Task 5 assignment and existing retrieval code/artifacts were read first. The exact assignment allowlist is enforced; the requested model was **`gpt-5-mini`**, and every response identified **`gpt-5-mini-2025-08-07`**. The installed OpenAI Python SDK is **2.8.1**, with **python-dotenv 1.2.1**. `pip check` passed. Reproducible dependency files are `solution/requirements-task5.txt` and `solution/requirements-task5.lock.txt`.

Credentials were explicitly loaded from the ignored project-root `.env`. No `OPENAI_BASE_URL` override was configured; calls used the default OpenAI Responses endpoint. `.env.example` contains no credential, and Git ignore behavior was verified. The configured credential was checked absent from deliverables without printing it. See `solution/rag/TASK5_USAGE.md` for setup and correction commands.

The SDK request uses documented `model`, `instructions`, `input`, `max_output_tokens=4096`, and `store=False`; sampling and reasoning overrides are omitted. The output allowance includes reasoning tokens. See the official [Responses reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create) and [GPT-5 mini model page](https://developers.openai.com/api/docs/models/gpt-5-mini).

`solve_task(textual_task, target_metadata, ...)` accepts behavior text separately from the target file/class/method. The batch CLI reads the unchanged manifest at `../missing_code.json`; this workspace has no `Assignments/missing_code.json`, but `--tasks` accepts either path. For each task, the pipeline uses Task 4's unchanged shared query builder and retrieves exactly five chunks. It sends all five original texts, the textual task, target metadata, and the current target method. It does not send the full repository or expand context-reference chunks.

The frozen Task 2/3 index represents source commit `b17f75374a6d63f0f245e472bb707e658c1b3cf7`; the working clone now contains generated changes. No chunking, embedding, or retrieval-evaluation artifact was rebuilt or modified. Validation-driven regeneration reuses precisely the same five chunks and supplies explicit rejection feedback and the preceding response.

## Editing and evidence

`method_editing.py` resolves paths within the configured repository, locates the class/method using fresh AST positions after each earlier edit, and accepts exactly one matching method definition. It validates signature, annotations, decorators, existing docstring, non-placeholder body, and complete-file compilation. Only the method's implementation body is transplanted; original headers, decorators, docstrings, and surrounding bytes remain intact. Multiline string literal values are preserved during indentation conversion. Recoverable originals are saved, concurrent changes are rejected, and replacement is atomic. Returned text is never executed to perform patching.

Each task directory records its actual task/query, five ranked IDs/scores/source locations and original texts, complete prompt, returned code, requested/returned model, response ID, returned usage, validation status, recovery copies, and applied diff. Generation attempts have separate directories. SDK retries are disabled; at most two explicit transport retries and two code regenerations are allowed per task, with a 90-second request timeout. These counters are distinct and bounded.

| Method | Generation attempts | Final result |
| --- | ---: | --- |
| `OrderStatus.is_terminal` | 2 | Applied |
| `InventoryLedger.__contains__` | 1 | Applied |
| `Warehouse.stock_report` | 1 | Applied |
| `OrderStateMachine.transition` | 1 | Applied |
| `OrderLog.by_status` | 1 | Applied |
| `Customer.can_afford` | 3 | Applied |
| `Order.__len__` | 1 | Applied |
| `BulkDiscountPricing.price` | 1 | Applied |
| `EventBus.__contains__` | 1 | Applied |
| `Money.__bool__` | 2 | Applied |

The rejected `OrderStatus` response had unexpected indentation. Two `Customer` responses and one `Money` response introduced a docstring where none existed. All four were rejected before writing; replacement responses came from the pipeline. No hand-written correction was applied.

Actual aggregate usage across all 14 responses: **71,443 input tokens**, **11,732 output tokens**, **83,175 total tokens**. The API reported **10,432 reasoning tokens** within output and **21,888 cached input tokens** within input. These are sums of returned usage fields, not local estimates. Monetary cost was not calculated.

## Commands and tests

Executed from `Week_06_Implementation`; network access was enabled for dependency downloads and real API execution:

```bash
.venv/bin/python -m pip install --cache-dir /tmp/week06-pip-cache --retries 0 --timeout 30 -r solution/requirements-task5.txt
.venv/bin/python -m pip check
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python -m unittest discover -s solution/rag/tests -p test_solving.py -v > solution/artifacts/task5_offline_tests.log 2>&1
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python solution/rag/solve_tasks.py --tasks ../missing_code.json --repository solution/AI4SE_Playground --chunks solution/artifacts/chunks.jsonl --embeddings solution/artifacts/embeddings.npz --metadata solution/artifacts/embeddings.metadata.json --cache-dir .cache/huggingface --env-file .env > solution/artifacts/task5_cli_status.json
```

`HF_HUB_OFFLINE=1` keeps local query encoding offline; OpenAI SDK HTTPS calls remain enabled. All **13 focused offline tests passed**, using only generic toy methods and explicit SDK MockTransport fixtures. These tests cover response/signature/docstring validation, exact body editing, fresh AST positions, path/symlink escapes, concurrency, atomic backups/modes, multiline literals, configuration, retries, regeneration feedback, incomplete responses, and sanitized API errors. The actual ten prepared queries and five-chunk contexts were independently compared with Task 4's saved evaluation.

After all ten real implementations were applied, the pipeline invoked this exact interpreter/command from `solution/AI4SE_Playground/playground`:

```text
/home/myroslav/projects/SEwAI/Labs/Week_06/Week_06_Implementation/.venv/bin/python -m unittest discover -s tests -v
```

| Repository suite | Tests | Failures | Errors | Exit code |
| --- | ---: | ---: | ---: | ---: |
| Preserved baseline | 481 | 35 | 17 | 1 |
| After real generation | 481 | 0 | 0 | 0 |

The complete actual output is `solution/artifacts/final_tests.log`; command, exit status, baseline comparison, and empty remaining-failure list are in `final_tests.status.json`. Both are backed by the run's own test log/summary. There were no remaining failures to correct and no functional-test-driven regeneration was needed. Tests and unrelated production source were not edited.

## Final audit and limitations

`task5_final_verification.json` confirms all ten applied bodies match actual returned code, all edits reconstruct from saved responses, all generation attempts reuse the same original five chunks, and all 36 pre-existing assignment/evidence files are byte-unchanged. Byte-level scope checks and AST comparisons restrict changes to the ten implementation bodies in six production files. `generated_changes.patch` is the actual Git diff: 44 insertions, ten deletions. Git metadata remains intact.

Passing the existing suite does not prove every possible behavior, and top-five retrieval does not guarantee complete context. Structural validation proves editing scope, not semantic correctness. No unresolved failures or blockers remain. The bonus task and final packaging were not started.
