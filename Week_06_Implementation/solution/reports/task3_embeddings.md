# Task 3: Local chunk embeddings

## Inputs, model, and dependencies

Task 3 and the Task 2 JSONL, manifest, and verification report were read before implementation. The input is the existing **55 chunks**, unchanged, from repository commit `b17f75374a6d63f0f245e472bb707e658c1b3cf7`. Their JSONL SHA-256 is `24bde3c13cd887b7ad32bfddae1f5dc96cfc6ee345ea857b02fcf868c1ee4a39`.

The requested [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) is a compact, general-purpose **English** sentence/paragraph embedding model producing 384-dimensional vectors. It is not specialized for this repository's code. The resolved model revision is **`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`**. Actual computation used its Transformer, mean-pooling, and normalization modules locally, in float32 on CPU, with eager attention, evaluation mode, and inference mode. No embedding service or generative API was called.

Downloads succeeded after network approval. The existing project `.venv` runs CPython 3.12.16. Tested primary dependencies are PyTorch **2.9.1+cpu**, Sentence Transformers **5.1.2**, Transformers **4.57.3**, NumPy **2.3.5**, and Hugging Face Hub **0.36.0**. CUDA is absent from this PyTorch build. `requirements-task3.txt` pins these packages; `requirements-task3.lock.txt` pins all installed transitive dependencies. `pip check` passed. Model files are cached in `.cache/huggingface`; subsequent encoding and tests ran offline.

## Input representation and long inputs

Each embedding input consists of this prefix followed immediately by the complete, unchanged original chunk text:

```text
Path: <repository-relative path> (lines <start>-<end>)
Classes: <all distinct enclosing class names, or (none)>
Symbols: <first six distinct non-class qualified symbols in source order>

Source:
<original text>
```

When more than six symbols are available, the prefix states the omitted count; all source definitions remain in the text. The exact prefix and embedding-text hash are recorded per row. Task 2 context-reference chunks are not appended to this representation.

Actual configuration readings: serialized tokenizer limit **512**, Transformer position limit **512**, Sentence Transformers sequence limit **256**, and loaded tokenizer runtime limit **256**. The effective limit is their minimum: **256**. BERT adds **2** special tokens (`[CLS]`, `[SEP]`), leaving **254 payload tokens**. No configured limit was increased.

The uncased tokenizer measures the entire assembled input with `add_special_tokens=False` and `truncation=False`. Its exact token-ID stream is split into windows of at most **254 payload tokens**, with **32-token overlap** and stride **222**. The last window ends at the final token. Special tokens are added separately to every window; every prepared and padded model input is checked against the 256-token limit. Token IDs enter the model directly, without decoding/re-tokenizing or implicit text truncation. The prefix occurs once in the full stream and is not repeated per window.

Each window vector is L2-normalized. The chunk vector is the payload-length-weighted mean of its window vectors, followed by L2 normalization, then stored as float32. Float64 accumulation reduces rounding error. Overlap deliberately contributes context to both adjacent windows; it is not deduplicated during aggregation. Payload weighting gives short final windows less weight. `local_embeddings.TextEncoder` exposes this same processing for later query encoding.

## Storage and reproducible commands

`embeddings.npz` stores `embeddings` (float32 matrix) and `chunk_ids` (fixed-width Unicode, no objects), in unchanged JSONL row order. `chunks.jsonl` remains the text store. `embeddings.metadata.json` records both artifact hashes, the source-manifest reference/hash and repository commit, model revision, dimensions, dtype, normalization, input representation, tokenizer limits, window ranges/weights, dependency versions, and verification results. `load_embedding_store` checks hashes and row IDs and always uses `np.load(..., allow_pickle=False)`.

Executed from `Week_06_Implementation`:

```bash
.venv/bin/python -m pip install --cache-dir /tmp/week06-pip-cache --retries 0 --timeout 30 -r solution/requirements-task3.txt
.venv/bin/python -m pip check
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python solution/rag/embed_repository.py solution/artifacts/chunks.jsonl solution/artifacts/embeddings.npz --cache-dir .cache/huggingface --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 --offline > solution/artifacts/task3_execution.json
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 .venv/bin/python -m unittest discover -s solution/rag/tests -v > solution/artifacts/task3_tests.log 2>&1
```

The pinned snapshot was downloaded beforehand using `HfApi.model_info` and `snapshot_download`, limited to JSON/text configuration, tokenizer files, and `model.safetensors`. On another machine, omit `--offline` and `HF_HUB_OFFLINE=1` on the encoding command to download the same pinned snapshot. For the exact tested package environment, install `-r solution/requirements-task3.lock.txt` instead of the primary requirements file.

Later query encoding can use `TextEncoder.from_metadata(metadata_path, cache_dir=...)` and `encoder.encode_texts([query_text])`, returning vectors and window details. Queries use plain text with the same pinned model, limits, aggregation, and normalization. No retrieval is implemented here.

## Actual verification results

| Measurement | Result |
| --- | --- |
| Stored vectors / dimensions | 55 / 384 |
| Source tokens, without specials: min / median / mean / max | 253 / 870 / 923.091 / 1,620 |
| Prefix + source tokens, without specials: min / median / mean / max | 337 / 986 / 1,037.764 / 1,774 |
| Total input tokens before window overlap and specials | 57,077 |
| Chunks requiring multiple windows | 55 of 55 |
| Windows / windows per chunk | 277 / 2–8 |
| Actual model-input tokens per window, including specials | 35–256 |
| Processed tokens, including overlap and specials | 64,735 |
| Final L2 norm range | 0.9999999404–1.0 |
| Compressed NPZ / metadata JSON | 81,640 / 79,474 bytes |
| Uncompressed numeric matrix / Unicode IDs | 84,480 / 14,080 bytes |

All values are finite and nonzero; IDs are unique and match the original 55 rows. Full token coverage and limits were checked for every actual chunk. Saving and reloading preserved IDs and numerical values exactly. The entire corpus was encoded twice: maximum absolute difference **0.0**, passing `atol=1e-6, rtol=1e-5`. This is a same-environment observation, not a promise of identical results across hardware or library versions.

All **6 integration tests passed**: storage/provenance, corpus-wide token coverage and limits, boundary/invalid-input cases, a pinned CPU query encoder versus standard short-text encoding, independent aggregation of the longest actual input, and rejection of mismatched storage/source files. Results are in `task3_tests.log`; execution measurements are in `task3_execution.json` and the metadata.

`task3_preservation.json` confirms all 17 pre-existing assignment/evidence files are byte-unchanged, all repository source hashes still match Task 2, all 10 target methods remain `pass`, and Git metadata and a clean working tree are preserved. The baseline tests were not rerun or repaired. Retrieval quality has **not yet been evaluated**; window aggregation may dilute specific code details. No top-n retrieval or code generation was implemented. Task 3 has no remaining blocker.
