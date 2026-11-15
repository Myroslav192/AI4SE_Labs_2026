#!/usr/bin/env python3
"""Embed an existing chunk JSONL locally; preserve its IDs and row order.

Usage: python embed_repository.py CHUNKS.jsonl OUTPUT.npz [options]
Downloads public weights if needed; never calls an inference API.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata as packages
import json
import os
from pathlib import Path
import platform
import statistics
import sys

import numpy as np

from local_embeddings import MODEL_ID, REPRESENTATION, TextEncoder, chunk_prefix, chunk_text


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def statistics_for(values: list[int]) -> dict:
    return {"min": min(values), "median": statistics.median(values), "mean": round(statistics.mean(values), 3), "max": max(values), "sum": sum(values)}


def load_chunks(path: Path, manifest_path: Path) -> tuple[list[dict], dict]:
    raw = path.read_bytes()
    chunks = [json.loads(line) for line in raw.splitlines()]
    manifest = json.loads(manifest_path.read_bytes())
    if sha256(raw) != manifest["chunks_sha256"]:
        raise ValueError("Chunk JSONL hash differs from the Task 2 manifest")
    if not chunks or len(chunks) != manifest["chunk_count"] or len({c["id"] for c in chunks}) != len(chunks):
        raise ValueError("Chunk count or IDs invalid")
    sources = {f["path"]: f["sha256"] for f in manifest["files"]}
    for chunk in chunks:
        if chunk["repository_commit"] != manifest["repository_commit"] or chunk["source_sha256"] != sources[chunk["path"]]:
            raise ValueError("Chunk source provenance differs from manifest")
    return chunks, manifest


def load_embedding_store(npz_path: Path, metadata_path: Path, chunks_path: Path):
    """Hash-checked loading for Task 4. Unicode IDs require no pickle."""
    metadata = json.loads(Path(metadata_path).read_bytes())
    if sha256(Path(chunks_path).read_bytes()) != metadata["source"]["chunks_sha256"]:
        raise ValueError("Chunk JSONL does not match these vectors")
    if sha256(Path(npz_path).read_bytes()) != metadata["storage"]["npz_sha256"]:
        raise ValueError("NPZ does not match embedding metadata")
    with np.load(npz_path, allow_pickle=False) as stored:
        if set(stored.files) != {"embeddings", "chunk_ids"}:
            raise ValueError("Unexpected NPZ arrays")
        vectors, ids = stored["embeddings"].copy(), stored["chunk_ids"].copy()
    chunks = [json.loads(line) for line in Path(chunks_path).read_bytes().splitlines()]
    if ids.dtype.kind != "U" or ids.tolist() != [c["id"] for c in chunks]:
        raise ValueError("Stored row IDs differ from the JSONL order")
    if vectors.dtype != np.float32 or vectors.shape != (len(chunks), metadata["model"]["dimensions"]):
        raise ValueError("Unexpected matrix dtype or shape")
    if not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors, axis=1), 1.0, rtol=0, atol=1e-5):
        raise ValueError("Stored vectors are not finite unit vectors")
    return vectors, ids, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chunks", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--revision", default="main", help="Use the resolved commit for reproducible runs")
    parser.add_argument("--overlap", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    metadata_path = (args.metadata or output.with_suffix(".metadata.json")).resolve()
    manifest_path = (args.source_manifest or args.chunks.with_suffix(".manifest.json")).resolve()
    protected = {args.chunks.resolve(), manifest_path}
    if output in protected or metadata_path in protected or output == metadata_path:
        parser.error("Outputs must not overwrite inputs or each other")
    chunks, manifest = load_chunks(args.chunks, manifest_path)
    input_hash, manifest_hash = sha256(args.chunks.read_bytes()), sha256(manifest_path.read_bytes())
    encoder = TextEncoder(
        revision=args.revision, cache_dir=args.cache_dir, overlap=args.overlap,
        batch_size=args.batch_size, threads=args.threads, local_files_only=args.offline,
    )
    texts = [chunk_text(chunk) for chunk in chunks]
    vectors, details = encoder.encode_texts(texts)
    ids = np.asarray([chunk["id"] for chunk in chunks], dtype=np.str_)
    if vectors.shape != (len(chunks), 384) or not np.isfinite(vectors).all():
        raise ValueError("Invalid embedding matrix")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1, atol=1e-5, rtol=0):
        raise ValueError("Final vectors are not unit length")
    # Repeat the entire actual corpus, not just one selected short input.
    repeated, repeated_details = encoder.encode_texts(texts)
    if details != repeated_details or not np.allclose(vectors, repeated, rtol=1e-5, atol=1e-6):
        raise ValueError("Repeated encoding exceeded rtol=1e-5, atol=1e-6")
    if input_hash != sha256(args.chunks.read_bytes()) or manifest_hash != sha256(manifest_path.read_bytes()):
        raise ValueError("Input artifacts changed during encoding")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        np.savez_compressed(handle, embeddings=vectors, chunk_ids=ids)
    with np.load(output, allow_pickle=False) as saved:
        roundtrip = np.array_equal(saved["chunk_ids"], ids) and np.array_equal(saved["embeddings"], vectors)
    if not roundtrip:
        raise ValueError("Save/reload changed IDs or numeric values")
    rows = []
    for row, (chunk, text, detail) in enumerate(zip(chunks, texts, details)):
        rows.append({
            "row": row, "chunk_id": chunk["id"], "path": chunk["path"],
            "prefix": chunk_prefix(chunk), "embedding_text_sha256": sha256(text.encode("utf-8")),
            "source_tokens_without_special": len(encoder.tokenize(chunk["text"])), **detail,
        })
    all_window_lengths = [length for detail in details for length in detail["window_model_input_tokens"]]
    metadata = {
        "schema_version": "local-chunk-embeddings-v1",
        "model": {"identifier": MODEL_ID, "resolved_revision": encoder.revision, "dimensions": encoder.dimensions,
                  "modules": [type(module).__name__ for module in encoder.model],
                  "tokenizer_class": type(encoder.tokenizer).__name__, "tokenizer_lowercase": encoder.tokenizer.do_lower_case},
        "source": {
            "chunks_path": os.path.relpath(args.chunks.resolve(), metadata_path.parent), "chunks_sha256": input_hash,
            "manifest_path": os.path.relpath(manifest_path, metadata_path.parent), "manifest_sha256": manifest_hash,
            "repository_commit": manifest["repository_commit"],
        },
        "input_representation": {
            "version": REPRESENTATION, "original_text_unchanged": True,
            "prefix": "Path and line range; all enclosing class names; first six distinct non-class symbol names in source order, with omitted count; blank line; Source:",
            "prefix_repeated_per_window": False, "query_representation": "plain query text via TextEncoder.from_metadata(...).encode_texts([...])",
            "tokenization": "complete assembled text, add_special_tokens=False, truncation=False; exact token IDs are windowed without decoding",
        },
        "encoding": encoder.settings(),
        "dependencies": {dist.metadata["Name"]: dist.version for dist in sorted(packages.distributions(), key=lambda d: d.metadata["Name"].lower())},
        "runtime": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine()},
        "storage": {
            "npz_path": os.path.relpath(output, metadata_path.parent), "npz_sha256": sha256(output.read_bytes()),
            "matrix_key": "embeddings", "ids_key": "chunk_ids", "row_order": "unchanged input JSONL order",
            "shape": list(vectors.shape), "dtype": str(vectors.dtype), "ids_dtype": str(ids.dtype),
            "allow_pickle": False, "compressed_npz_bytes": output.stat().st_size,
            "matrix_uncompressed_bytes": vectors.nbytes, "ids_uncompressed_bytes": ids.nbytes,
        },
        "corpus_statistics": {
            "chunks": len(chunks), "source_tokens_without_special": statistics_for([r["source_tokens_without_special"] for r in rows]),
            "embedding_input_tokens_without_special": statistics_for([d["input_tokens_without_special"] for d in details]),
            "embedding_input_tokens_with_special_if_unsplit": statistics_for([d["input_tokens_with_special_if_unsplit"] for d in details]),
            "window_model_input_tokens": statistics_for(all_window_lengths),
            "total_windows": len(all_window_lengths), "multi_window_chunks": sum(d["window_count"] > 1 for d in details),
        },
        "verification": {
            "all_tokens_covered": all(d["full_token_coverage"] for d in details),
            "all_windows_within_effective_limit": max(all_window_lengths) <= encoder.limit,
            "finite_values": bool(np.isfinite(vectors).all()), "unique_matching_ids": len(set(ids.tolist())) == len(chunks),
            "norm_min": float(norms.min()), "norm_max": float(norms.max()), "norm_absolute_tolerance": 1e-5,
            "save_reload_ids_and_values_exact": bool(roundtrip),
            "repeated_encoding_full_corpus": True, "repeat_atol": 1e-6, "repeat_rtol": 1e-5,
            "repeat_max_absolute_difference": float(np.max(np.abs(vectors - repeated))),
        },
        "rows": rows,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    load_embedding_store(output, metadata_path, args.chunks)
    print(json.dumps({"model_revision": encoder.revision, "limits": encoder.limits,
                      "storage": metadata["storage"], "statistics": metadata["corpus_statistics"],
                      "verification": metadata["verification"]}, indent=2))


if __name__ == "__main__":
    main()
