#!/usr/bin/env python3
"""Exact cosine retrieval over the existing chunk embeddings, entirely on CPU.

Use ChunkRetriever for repeated queries or retrieve_chunks for a single query.
The CLI writes JSON to stdout and reports invalid inputs/artifacts on stderr.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from numbers import Integral
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

import numpy as np

from embed_repository import load_chunks, load_embedding_store
from local_embeddings import AGGREGATION, MODEL_ID, REPRESENTATION, TextEncoder, chunk_text


QUERY_BUILDER_VERSION = "file-class-method-description-v1"


class ArtifactError(ValueError):
    """An artifact is missing, corrupt, or incompatible with this encoder."""


def validate_n(n: int) -> int:
    if isinstance(n, bool) or not isinstance(n, Integral) or n <= 0:
        raise ValueError("n must be a positive integer (booleans are not accepted)")
    return int(n)


def build_task_query(task: Mapping) -> str:
    """Task 4/5 shared template; use the supplied behavior without paraphrasing."""
    if not isinstance(task, Mapping):
        raise ValueError("Task must be a mapping")
    for key in ("file", "class", "method"):
        if not isinstance(task.get(key), str) or not task[key].strip():
            raise ValueError(f"Task requires a nonempty '{key}' string")
    description = task.get("description", task.get("docstring"))
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Task requires a description or docstring string")
    description = description.strip()
    if description[:3] in ('"""', "'''") and description.endswith(description[:3]):
        description = description[3:-3].strip()
    if not description:
        raise ValueError("Task description must not be empty")
    return (
        f'Implement {task["class"]}.{task["method"]} in {task["file"]}.\n'
        f"Required behavior: {description}"
    )


def rank_vectors(vectors: np.ndarray, chunk_ids: np.ndarray, query: np.ndarray, n: int):
    """Return (row_indices, all_scores). Rank only by cosine, then chunk ID.

    Corpus rows must already be unit vectors. Float64 dot products reduce
    accumulation error; no rounding, score adjustment, or near-tie grouping.
    """
    n = validate_n(n)
    matrix = np.asarray(vectors)
    ids = np.asarray(chunk_ids)
    query = np.asarray(query, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] < 1 or ids.shape != (matrix.shape[0],):
        raise ValueError("Nonempty matrix and one chunk ID per row are required")
    if ids.dtype.kind != "U" or len(set(ids.tolist())) != len(ids):
        raise ValueError("Chunk IDs must be distinct Unicode strings")
    if query.shape != (matrix.shape[1],) or not np.isfinite(query).all():
        raise ValueError("Query vector has invalid dimensions or nonfinite values")
    if not np.isfinite(matrix).all() or not np.allclose(np.linalg.norm(matrix, axis=1), 1, rtol=0, atol=1e-5):
        raise ValueError("Corpus vectors must be finite unit vectors")
    norm = np.linalg.norm(query)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError("Query vector must have a finite nonzero norm")
    scores = matrix.astype(np.float64) @ (query / norm)
    order = np.lexsort((ids, -scores))[:min(n, len(ids))]
    return order, scores


class ChunkRetriever:
    """Validate artifacts and load the pinned local encoder once for reuse."""

    def __init__(self, chunks_path, embeddings_path, metadata_path, *, cache_dir=None, source_manifest=None):
        self.chunks_path = Path(chunks_path)
        self.embeddings_path = Path(embeddings_path)
        self.metadata_path = Path(metadata_path)
        try:
            metadata = json.loads(self.metadata_path.read_bytes())
            if metadata["schema_version"] != "local-chunk-embeddings-v1":
                raise ValueError("Unsupported embedding schema version")
            model, storage = metadata["model"], metadata["storage"]
            if model["identifier"] != MODEL_ID or model["dimensions"] != 384:
                raise ValueError("Incompatible model identifier or dimensions")
            if not re.fullmatch(r"[0-9a-f]{40}", model["resolved_revision"]):
                raise ValueError("Model revision must be a resolved 40-character commit")
            if metadata["input_representation"]["version"] != REPRESENTATION:
                raise ValueError("Incompatible embedding input representation")
            if metadata["encoding"]["aggregation"] != AGGREGATION or metadata["encoding"]["normalization"] != "L2, per window and after aggregation":
                raise ValueError("Incompatible aggregation or normalization")
            if (storage["dtype"], storage["matrix_key"], storage["ids_key"], storage["allow_pickle"], storage["row_order"]) != ("float32", "embeddings", "chunk_ids", False, "unchanged input JSONL order"):
                raise ValueError("Incompatible storage layout")
            self.source_manifest_path = Path(source_manifest) if source_manifest else self.metadata_path.parent / metadata["source"]["manifest_path"]
            if hashlib.sha256(self.source_manifest_path.read_bytes()).hexdigest() != metadata["source"]["manifest_sha256"]:
                raise ValueError("Source-manifest hash differs from embedding metadata")
            self.chunks, self.source_manifest = load_chunks(self.chunks_path, self.source_manifest_path)
            # Own/close the ZIP handle even for invalid archives: NumPy's NPZ
            # constructor can otherwise leave its internally opened file unclosed.
            with ZipFile(self.embeddings_path) as archive:
                if archive.testzip() is not None:
                    raise ValueError("Corrupt NPZ ZIP member (CRC mismatch)")
            self.vectors, self.ids, self.metadata = load_embedding_store(self.embeddings_path, self.metadata_path, self.chunks_path)
            if self.vectors.shape[0] < 1 or len(set(self.ids.tolist())) != len(self.chunks):
                raise ValueError("Corpus must be nonempty with unique IDs")
            if storage["shape"] != list(self.vectors.shape) or storage["ids_dtype"] != str(self.ids.dtype):
                raise ValueError("Stored matrix/ID declaration differs from NPZ")
            if metadata["source"]["repository_commit"] != self.source_manifest["repository_commit"]:
                raise ValueError("Repository commits differ between manifests")
            if len(metadata["rows"]) != len(self.chunks):
                raise ValueError("Embedding row metadata count differs from chunks")
            for index, (chunk, row) in enumerate(zip(self.chunks, metadata["rows"])):
                if row["row"] != index or row["chunk_id"] != chunk["id"]:
                    raise ValueError("Embedding row metadata differs from chunk IDs/order")
                if row["embedding_text_sha256"] != hashlib.sha256(chunk_text(chunk).encode("utf-8")).hexdigest():
                    raise ValueError("Embedding-text hash differs from the chunk representation")
        except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, EOFError, BadZipFile) as error:
            raise ArtifactError(f"Cannot load compatible retrieval artifacts: {error}") from error
        try:
            self.encoder = TextEncoder.from_metadata(self.metadata_path, cache_dir=cache_dir, local_files_only=True)
            if type(self.encoder.tokenizer).__name__ != model["tokenizer_class"] or self.encoder.tokenizer.do_lower_case != model["tokenizer_lowercase"]:
                raise ValueError("Tokenizer differs from stored model metadata")
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            raise ArtifactError(f"Cannot load compatible local query encoder; check --cache-dir and pinned model files: {error}") from error
        self.last_query_encoding = None

    def search(self, task: str, n: int = 5) -> list[dict]:
        n = validate_n(n)
        if not isinstance(task, str) or not task.strip():
            raise ValueError("Textual task must be a nonempty string")
        query, plans = self.encoder.encode_texts([task])
        self.last_query_encoding = plans[0]
        order, scores = rank_vectors(self.vectors, self.ids, query[0], n)
        results = []
        for rank, index in enumerate(order, start=1):
            chunk = self.chunks[int(index)]
            results.append({
                "rank": rank, "chunk_id": chunk["id"], "score": float(scores[index]),
                "path": chunk["path"], "start_line": chunk["start_line"], "end_line": chunk["end_line"],
                "symbols": deepcopy(chunk.get("symbols", [])),
                "enclosing_classes": list(chunk.get("enclosing_classes", [])),
                "context_chunk_ids": list(chunk.get("context_chunk_ids", [])), "text": chunk["text"],
            })
        return results


def retrieve_chunks(task: str, n: int = 5, *, chunks_path, embeddings_path, metadata_path, cache_dir=None, source_manifest=None) -> list[dict]:
    """Single-query convenience function; use ChunkRetriever to reuse the model."""
    validate_n(n)
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Textual task must be a nonempty string")
    return ChunkRetriever(chunks_path, embeddings_path, metadata_path, cache_dir=cache_dir, source_manifest=source_manifest).search(task, n)


def positive_integer(value: str) -> int:
    try:
        return validate_n(int(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError("n must be a positive integer") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Textual programming task/query")
    parser.add_argument("--chunks", required=True, type=Path)
    parser.add_argument("--embeddings", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("-n", "--n", type=positive_integer, default=5)
    args = parser.parse_args()
    try:
        results = retrieve_chunks(args.task, args.n, chunks_path=args.chunks, embeddings_path=args.embeddings,
                                  metadata_path=args.metadata, cache_dir=args.cache_dir, source_manifest=args.source_manifest)
    except (ArtifactError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({"query": args.task, "requested_n": args.n, "returned_n": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
