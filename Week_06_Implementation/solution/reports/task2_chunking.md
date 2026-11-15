# Task 2: Repository chunking

## Environment and inspected inputs

Task 2 was re-read from `../Task_2/Task_2.md`. Checks covered `python3`, `python`, versioned Python commands, existing environments, common interpreter locations, and managers including uv, pyenv, Conda/Mamba, mise, asdf, and Poetry. No usable interpreter or manager was found. A portable CPython **3.12.16**, from the official [Astral release 20261110](https://github.com/astral-sh/python-build-standalone/releases/tag/20261110), was downloaded after network approval. Its archive SHA-256 matched the release asset digest:

`c2f87d4b4e8db3abddb0f116c6ccfc503d0cbdbb9ee8faacddad1b679ec12e99`

The actual environment creation command, from the assignment working directory, was:

```bash
/tmp/week06-python-runtime/python/bin/python3 -m venv .venv
```

`.venv/bin/python --version` returned `Python 3.12.16`; pip was also verified. The chunker uses only the standard library and requires Python 3.10+. This environment depends on the base runtime in `/tmp`; recreate it if that runtime is cleaned up. No system installation or third-party packages were needed.

The unchanged checkout is commit **`b17f75374a6d63f0f245e472bb707e658c1b3cf7`**. File lengths were measured before selecting limits: 28 tracked files, 4,596 lines, and 164,226 bytes. The largest file, `playground/tests/test_models.py`, has 497 lines and 19,004 characters. The layout contains 13 package modules, 13 test modules, an empty test-package initializer, and `.gitignore`. There is no upstream README, dependency manifest, packaging configuration, or documented test command.

## Splitting and context

The defaults are **120 lines and 6,000 Unicode characters per chunk**, with **zero overlapping source lines**. These limits divide the larger classes and test modules while preserving ordinary methods. They are line/character budgets, not measured token budgets.

Python's AST supplies boundaries before top-level statements and definitions, including decorators. Oversized classes expose boundaries before their direct body statements and methods. Adjacent sections are greedily packed within both limits. Every source line, including comments, blank lines, imports, module constants, and class attributes, belongs to exactly one chunk. Source text is sliced directly from UTF-8 input without reformatting, dedenting, or newline normalization.

Oversized indivisible sections, non-Python text, and Python files with syntax errors use whole-line windows. A single line longer than 6,000 characters is retained intact and explicitly marked as a size exception. Parse errors are recorded. In this checkout, only `.gitignore` needs line-window fallback; no Python function is split and there are no size exceptions.

Each chunk contains its repository-relative path, inclusive 1-based line range, original `text`, source SHA-256, indexed commit, size measurements, intersecting qualified symbols, and enclosing classes. Its ID is SHA-256 of the canonical JSON list `[schema_version, path, source_sha256, start_line, end_line]`. IDs are reproducible for unchanged inputs; editing a file changes its source hash and its chunk IDs.

`context_chunk_ids` reference chunks containing module preamble/imports/constants and relevant class headers/docstrings/attributes. No context text is duplicated or prepended. Later consumers must follow these references when needed; the per-chunk limits do not bound an assembled prompt containing additional context.

## Inclusion, exclusion, and provenance

The policy accepts Python and common source formats, documentation, and project configuration, including Markdown, reStructuredText, TOML, YAML, JSON, requirements text, and `.gitignore`. All 28 tracked files in this checkout are eligible. All 27 nonempty files contribute chunks; `playground/tests/__init__.py` is recorded in the manifest with its empty-file hash and zero chunks.

The scanner prunes Git metadata, virtual environments (including custom directories identified by `pyvenv.cfg`), caches, build output, solution/artifact/report/generated directories, and conventional secret directories and filenames. It rejects symlinks, unsupported/generated file types, non-UTF-8 files, and binary/control-character content. The actual excluded directory is `.git`. Output files are explicitly excluded if placed within the scanned tree.

`chunks.manifest.json` records the commit, tracked-file Git status, limits, every included file's raw SHA-256/bytes/characters/lines, exclusions, parse errors, and the JSONL SHA-256. It includes no timestamp or absolute source path. The JSONL digest is:

`24bde3c13cd887b7ad32bfddae1f5dc96cfc6ee345ea857b02fcf868c1ee4a39`

## Execution and verification

Executed from `Week_06_Implementation`:

```bash
.venv/bin/python solution/rag/chunk_repository.py solution/AI4SE_Playground solution/artifacts/chunks.jsonl
.venv/bin/python solution/rag/verify_chunking.py solution/AI4SE_Playground solution/artifacts/chunks.jsonl ../missing_code.json > solution/artifacts/task2_verification.json
```

Both commands exited 0. The verifier independently compares source bytes with Git HEAD, loads every JSONL record, checks unique IDs and sorted paths/ranges, validates hashes and line slices, reconstructs every nonempty file exactly, checks context references and limits, and confirms complete coverage of all 10 unchanged `pass` methods. All **698** fitting function/method definitions, including nested functions and decorators, remain whole. The verifier runs the chunker again in a temporary directory: both JSONL and manifest are byte-identical.

| Measurement | Actual result |
| --- | --- |
| Eligible files / nonempty files | 28 / 27 |
| Chunks | 55 |
| Lines per chunk: min / median / mean / max | 23 / 85 / 83.56 / 120 |
| Characters per chunk: min / median / mean / max | 869 / 3,075 / 2,985.93 / 5,450 |
| Line-window chunks / size exceptions / parse errors | 2 / 0 / 0 |
| Missing-method locations covered | 10 / 10 |

Additional temporary fixtures verified exclusions, documentation/configuration inclusion, byte-exact CRLF preservation, decorated methods, oversized-method windows, the single-long-line exception, syntax-error retention, and deterministic reruns. Results are saved in `task2_edge_checks.json`; the clone was untouched.

## Baseline and limitations

Before implementing the chunker, the unchanged repository's tests were run **once** using the standard-library discovery command inferred in Task 1, since upstream documents none: `python -m unittest discover -s tests -v`, with working directory `solution/AI4SE_Playground/playground`. The actual interpreter command is recorded in `baseline_tests.json`; complete output is in `baseline_tests.log`. Result: **481 tests, 35 failures, 17 errors, exit code 1**. Existing failures were not repaired, and tests were not rerun.

Secret exclusion is filename/directory based, not a guarantee against secrets embedded in ordinary source. The text-format allowlist intentionally excludes other encodings and unsupported formats. AST parsing does not resolve imports or dependencies; syntax-error and oversized-section windows may divide semantic units. Retrieval quality and model token usage have not been evaluated.

The clone remains clean with Git metadata intact. All 10 target methods remain unimplemented. Repository tests, assignment files, and Task 1 evidence are unchanged; no embeddings or model API calls were made. Task 2 has no remaining blocker.
