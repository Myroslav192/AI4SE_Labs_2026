#!/usr/bin/env python3
"""Independently verify an index against Git, source lines, ASTs, and the task manifest.

Usage: python verify_chunking.py REPOSITORY CHUNKS.jsonl MISSING_CODE.json
Prints a JSON verification summary. Does not run the repository tests.
"""

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("chunks", type=Path)
    parser.add_argument("missing_code", type=Path)
    args = parser.parse_args()
    repo, output = args.repository.resolve(), args.chunks.resolve()
    manifest_path = output.with_suffix(".manifest.json")
    manifest = json.loads(manifest_path.read_bytes())
    chunks = [json.loads(line) for line in output.read_bytes().splitlines()]
    by_id = {c["id"]: c for c in chunks}
    assert len(by_id) == len(chunks) == manifest["chunk_count"], "Duplicate IDs/count mismatch"
    assert [(c["path"], c["start_line"]) for c in chunks] == sorted((c["path"], c["start_line"]) for c in chunks), "Unsorted chunks"
    assert digest(output.read_bytes()) == manifest["chunks_sha256"]
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    assert commit == manifest["repository_commit"]
    assert subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain=v1"], text=True) == "", "Repository changed"
    tracked = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"]).decode().split("\0")[:-1]
    # This checkout contains no tracked files excluded by the eligibility policy.
    assert sorted(tracked) == sorted(f["path"] for f in manifest["files"]), "Eligible tracked-file coverage mismatch"
    assert len(manifest["files"]) == manifest["file_count"]
    max_lines, max_chars = manifest["limits"]["max_lines"], manifest["limits"]["max_characters"]
    files, preserved, exceptions = {}, 0, []

    for entry in manifest["files"]:
        path = entry["path"]
        raw = (repo / path).read_bytes()
        assert raw == subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{path}"]), f"Changed source: {path}"
        assert digest(raw) == entry["sha256"]
        text = raw.decode("utf-8")
        lines = text.splitlines(keepends=True)
        assert (len(raw), len(text), len(lines)) == (entry["bytes"], entry["characters"], entry["lines"])
        own = [c for c in chunks if c["path"] == path]
        cursor = 1
        for c in own:
            assert c["start_line"] == cursor, f"Gap/overlap in {path}"
            assert c["start_line"] <= c["end_line"] <= len(lines)
            assert c["text"] == "".join(lines[c["start_line"] - 1:c["end_line"]])
            assert c["source_sha256"] == entry["sha256"] and c["repository_commit"] == commit
            assert c["line_count"] == c["end_line"] - c["start_line"] + 1 <= max_lines
            assert c["character_count"] == len(c["text"])
            if len(c["text"]) > max_chars:
                assert c["line_count"] == 1 and c["size_exception"] == "single line exceeds character limit"
                exceptions.append(c["id"])
            else:
                assert c["size_exception"] is None
            for context in c["context_chunk_ids"]:
                assert context in by_id and context != c["id"] and by_id[context]["path"] == path
            cursor = c["end_line"] + 1
        assert cursor == len(lines) + 1
        assert "".join(c["text"] for c in own).encode("utf-8") == raw
        files[path] = (lines, own)
        if path.endswith(".py"):
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
                    end = node.end_lineno
                    if end - start + 1 <= max_lines and len("".join(lines[start - 1:end])) <= max_chars:
                        assert any(c["start_line"] <= start and c["end_line"] >= end for c in own), f"Split fitting function {path}:{start}"
                        preserved += 1

    missing = []
    for task in json.loads(args.missing_code.read_bytes()):
        path = task["file"]
        lines, own = files[path]
        tree = ast.parse("".join(lines))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == task["class"])
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == task["method"])
        assert len(method.body) == 1 and isinstance(method.body[0], ast.Pass), "Missing-method implementation changed"
        holder = next(c for c in own if c["start_line"] <= method.lineno and c["end_line"] >= method.end_lineno)
        qualified = f'{task["class"]}.{task["method"]}'
        assert qualified in [s["name"] for s in holder["symbols"]]
        assert task["class"] in holder["enclosing_classes"]
        reachable = [holder] + [by_id[i] for i in holder["context_chunk_ids"]]
        # Class definition, docstrings/attributes, imports, and module constants remain reachable.
        ranges = [(cls.lineno, cls.body[0].lineno - 1)]
        ranges.extend((n.lineno, n.end_lineno) for n in cls.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        ranges.extend((n.lineno, n.end_lineno) for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        for start, end in ranges:
            for line in range(start, end + 1):
                assert any(c["start_line"] <= line <= c["end_line"] for c in reachable), f"Unreachable context for {qualified}"
        missing.append({"symbol": qualified, "path": path, "start_line": method.lineno, "end_line": method.end_lineno, "chunk_id": holder["id"]})

    with tempfile.TemporaryDirectory(prefix="week06-chunks-repeat-") as tmp:
        repeat = Path(tmp) / output.name
        command = [sys.executable, str(Path(__file__).with_name("chunk_repository.py")), str(repo), str(repeat), "--max-lines", str(max_lines), "--max-chars", str(max_chars)]
        subprocess.run(command, check=True, capture_output=True)
        assert repeat.read_bytes() == output.read_bytes(), "Second run changed JSONL"
        assert repeat.with_suffix(".manifest.json").read_bytes() == manifest_path.read_bytes(), "Second run changed manifest"

    def sizes(field):
        values = [c[field] for c in chunks]
        return {"min": min(values), "median": statistics.median(values), "mean": round(statistics.mean(values), 2), "max": max(values)}

    print(json.dumps({
        "result": "PASS", "repository_commit": commit, "files": len(files),
        "nonempty_files": sum(bool(lines) for lines, _ in files.values()),
        "empty_files": [p for p, (lines, _) in files.items() if not lines],
        "source_lines": sum(len(lines) for lines, _ in files.values()),
        "source_bytes": sum(f["bytes"] for f in manifest["files"]),
        "chunks": len(chunks), "chunks_per_file": dict(sorted(Counter(c["path"] for c in chunks).items())),
        "chunk_lines": sizes("line_count"), "chunk_characters": sizes("character_count"),
        "fallback_chunks": sum(c["line_window_fallback"] for c in chunks), "size_exceptions": exceptions,
        "fitting_functions_preserved": preserved, "missing_methods": missing,
        "parse_errors": [f for f in manifest["files"] if f["parse_error"]],
        "second_run_jsonl_identical": True, "second_run_manifest_identical": True,
        "chunks_sha256": digest(output.read_bytes()),
    }, indent=2))


if __name__ == "__main__":
    main()
