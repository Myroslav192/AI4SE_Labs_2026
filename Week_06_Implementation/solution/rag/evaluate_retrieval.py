#!/usr/bin/env python3
"""Evaluate top-five target-span coverage without influencing ranking."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path

from retrieve_chunks import ArtifactError, ChunkRetriever, QUERY_BUILDER_VERSION, build_task_query


def target_span(task, repository, manifest):
    """Read the original target's full definition, including decorators."""
    raw = (repository / task["file"]).read_bytes()
    entry = next(f for f in manifest["files"] if f["path"] == task["file"])
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError(f'Target source differs from indexed source: {task["file"]}')
    tree = ast.parse(raw)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == task["class"])
    method = next(n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == task["method"])
    start = min([method.lineno] + [d.lineno for d in method.decorator_list])
    return {"path": task["file"], "start_line": start, "end_line": method.end_lineno, "source_sha256": entry["sha256"]}


def evaluate_tasks(tasks, retriever, repository):
    rows = []
    for task in tasks:
        query = build_task_query(task)
        ranked = retriever.search(query, n=5)
        # Ground truth is inspected after ranking and is never given to search.
        target = target_span(task, repository, retriever.source_manifest)
        hits = [result["rank"] for result in ranked if result["path"] == target["path"] and result["start_line"] <= target["start_line"] and result["end_line"] >= target["end_line"]]
        rows.append({"task": task, "query": query, "query_encoding": retriever.last_query_encoding,
                     "target_span": target, "target_method_hit": bool(hits),
                     "target_method_rank": min(hits) if hits else None, "results": ranked})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--chunks", required=True, type=Path)
    parser.add_argument("--embeddings", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        protected = {p.resolve() for p in (args.tasks, args.chunks, args.embeddings, args.metadata)}
        retriever = ChunkRetriever(args.chunks, args.embeddings, args.metadata, cache_dir=args.cache_dir, source_manifest=args.source_manifest)
        protected.add(retriever.source_manifest_path.resolve())
        if args.output.resolve() in protected:
            raise ValueError("Evaluation output must not overwrite an input artifact")
        tasks = json.loads(args.tasks.read_bytes())
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("Task manifest must be a nonempty list")
        rows = evaluate_tasks(tasks, retriever, args.repository)
    except (ArtifactError, OSError, ValueError, KeyError, TypeError, StopIteration, SyntaxError) as error:
        parser.error(str(error))
    hits = sum(row["target_method_hit"] for row in rows)
    report = {
        "schema_version": "top-five-target-span-evaluation-v1", "n": 5,
        "query_builder_version": QUERY_BUILDER_VERSION,
        "query_template": "Implement {class}.{method} in {file}.\nRequired behavior: {description}",
        "ranking": "float64 dot product with normalized query; descending score, ascending chunk ID for exact ties",
        "model": retriever.metadata["model"], "encoding": retriever.metadata["encoding"],
        "corpus_size": len(retriever.chunks), "repository_commit": retriever.source_manifest["repository_commit"],
        "inputs": {name: {"path": os.path.relpath(path.resolve(), args.output.resolve().parent), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in {"tasks": args.tasks, "chunks": args.chunks, "embeddings": args.embeddings, "metadata": args.metadata, "source_manifest": retriever.source_manifest_path}.items()},
        "summary": {"tasks": len(rows), "target_method_hits_at_5": hits, "target_method_misses_at_5": len(rows) - hits,
                    "hit_fraction": hits / len(rows), "missed_methods": [f'{r["task"]["class"]}.{r["task"]["method"]}' for r in rows if not r["target_method_hit"]]},
        "limitation": "Target-method coverage is only a diagnostic proxy; it does not prove retrieval of all necessary context or correctness of generated code. This small evaluation does not establish optimal retrieval quality.",
        "tasks": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
