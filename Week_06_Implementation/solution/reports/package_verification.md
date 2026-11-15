# Submission package verification

## Actual extraction checks

The archive was built from an explicit file selection, opened as a ZIP, checked
for CRC errors/duplicate names/unsafe paths, and extracted into a new temporary
directory. All entries are ordinary regular files. The archive contains the
solved repository's 28 project files, not a submodule/gitlink; its live `.git`
directory was never removed. The seven original assignment files were copied
byte-for-byte into `Assignments/`, including `missing_code.json`.

Candidate verification completed with **PASS**. The actual machine-readable
[candidate receipt](../artifacts/package_candidate_verification.json) is labeled
as the candidate before final documentation; its counts describe that candidate,
not a claim that later archive bytes were identical. The complete extracted-copy
[repository test output](../artifacts/package_repository_tests.log) and
[offline pipeline test output](../artifacts/package_pipeline_offline_tests.log)
are retained. Historical Task 1–5 evidence was not rewritten.

| Check | Actual result |
| --- | --- |
| Original assignments | 7 copies match source hashes |
| Original repository tests | All 14 test-package files match the frozen original source |
| Solved repository | All 28 ordinary project files match the live solved copy |
| Intended implementations | 10/10 method bodies match accepted real model responses; signatures/decorators/docstrings preserved |
| Generation evidence | 14 real responses, ten accepted methods, four original rejections retained |
| Frozen original source | All 28 files reconstruct from the chunks and match recorded source hashes |
| Embedding correspondence | 55 unique IDs in JSONL order; 55 × 384 finite unit float32 vectors; `allow_pickle=False` |
| Recorded artifact hashes | Chunk JSONL, source manifest, NPZ and embedding-text row hashes match |
| Extracted repository tests | **481 tests, 0 failures, 0 errors, exit 0** |
| Offline pipeline tests | **13 passed**, explicit toy/MockTransport fixtures only |
| Pipeline CLI help | Chunking, chunk verification, embedding, retrieval, evaluation and generation all exit 0 |
| Actual extracted-copy retrieval | Five results match saved CLI IDs and scores within `atol=1e-6, rtol=1e-5` |
| Local Markdown links | All local targets resolve in the extracted layout |
| Credentials | No configured secret or checked credential signature found; `.env` absent |
| Exclusions | No Git metadata, virtual environments, weights/caches, bytecode, staging files or nested submission ZIP |

The automated verifier does not fetch external websites. Separately, the four
linked reference pages and original repository page were opened successfully
through the web tool; [link-check evidence](../artifacts/package_external_links.json)
records this without inventing HTTP status codes. No model API call was made.

## Finalization and integrity

After adding this report and the actual check logs, the archive and `SHA256SUMS`
are regenerated. The final ZIP is extracted again and the same static checks,
repository tests, CLI checks, offline tests, and local retrieval are rerun on
that final version. The separate root-level
`Week06_RAG_submission.verification.json` records the final pass, file counts,
and binary ZIP digest. It is outside the ZIP to avoid a self-referential digest.
The sibling `Week06_RAG_submission.zip.sha256` authenticates the delivered ZIP
against its recorded digest (not a digital signature).

Inside the archive, `SHA256SUMS` enumerates every payload file except itself,
including this report. Its path set and every SHA-256 value are checked against
the actual final extracted contents. To repeat these checks:

```bash
.venv/bin/python solution/tools/verify_submission.py --root .
sha256sum -c SHA256SUMS
```

The build and extraction-check implementation is included under `solution/tools/`.
Generation and live-source files are unchanged by packaging. The bonus report
has 693 whitespace-separated words and is a proposal, not an additional experiment.

## Limits of verification

Checks reused the available CPython 3.12.16 project environment and its cached
MiniLM model. No clean-environment installation, new dependency download,
embedding regeneration, alternative retrieval experiment, or new generation
request was performed. The archive intentionally excludes the interpreter,
installed dependencies, cached weights, and credentials; recipients follow
`SUBMISSION.md` to supply them. Exact-secret matching and credential-pattern
scanning are practical checks, not a proof that arbitrary unknown secret formats
could never exist. Existing tests passing does not establish unseen-case correctness.
