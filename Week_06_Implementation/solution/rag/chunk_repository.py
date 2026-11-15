#!/usr/bin/env python3
"""Deterministic, lossless repository chunking using only the standard library.

Usage: python chunk_repository.py REPOSITORY OUTPUT.jsonl
Writes OUTPUT.manifest.json alongside the JSONL. Requires Python 3.10+.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess


VERSION = "ast-lines-v1"
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", ".env", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache", ".tox", ".nox",
    "node_modules", "build", "dist", "htmlcov", "coverage", ".idea", ".vscode",
    "solution", "artifacts", "reports", "generated", ".aws", ".ssh", "secrets",
}
TEXT_SUFFIXES = {
    ".py", ".pyi", ".md", ".rst", ".txt", ".toml", ".ini", ".cfg", ".json",
    ".jsonc", ".yaml", ".yml", ".xml", ".sh", ".bash", ".sql", ".js", ".jsx",
    ".ts", ".tsx", ".html", ".css", ".scss", ".lock",
}
TEXT_NAMES = {".gitignore", ".gitattributes", ".editorconfig", "dockerfile", "makefile", "license", "notice", "readme"}
DEFINITIONS = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def secret_name(name: str) -> bool:
    name = name.lower()
    return (
        name.startswith((".env", "secrets.", "secret.", "credentials.", "tokens."))
        or name in {"secrets", "credentials", ".netrc", ".pypirc", "id_rsa", "id_ed25519"}
        or Path(name).suffix in {".pem", ".key", ".p12", ".pfx", ".keystore"}
    )


def source_files(repo: Path, outputs: set[Path]) -> tuple[list[Path], list[dict]]:
    """Prune excluded directories before reading files; never follow symlinks."""
    included, excluded = [], []
    for directory, dirs, files in os.walk(repo, followlinks=False):
        parent = Path(directory)
        for name in sorted(dirs[:]):
            path = parent / name
            reason = None
            if path.is_symlink():
                reason = "symlink"
            elif name.lower() in EXCLUDED_DIRS or name.endswith((".egg-info", ".dist-info")) or secret_name(name):
                reason = "excluded directory"
            elif (path / "pyvenv.cfg").is_file():
                reason = "virtual environment"
            if reason:
                dirs.remove(name)
                excluded.append({"path": path.relative_to(repo).as_posix(), "reason": reason})
        dirs.sort()
        for name in sorted(files):
            path = parent / name
            reason = None
            if path.is_symlink():
                reason = "symlink"
            elif path.resolve() in outputs:
                reason = "generated output"
            elif secret_name(name):
                reason = "secret filename"
            elif path.suffix.lower() not in TEXT_SUFFIXES and name.lower() not in TEXT_NAMES:
                reason = "unsupported or generated file type"
            if reason:
                excluded.append({"path": path.relative_to(repo).as_posix(), "reason": reason})
            else:
                included.append(path)
    return sorted(included, key=lambda p: p.relative_to(repo).as_posix()), excluded


def definition_start(node: ast.AST) -> int:
    return min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])


def python_structure(text: str, lines: list[str], fits) -> tuple[list[int], list[dict], list[tuple[int, int]], dict[str, list[tuple[int, int]]]]:
    """Find safe boundaries, symbols, and references to module/class context."""
    tree = ast.parse(text)
    cuts = {1, len(lines) + 1}
    symbols, module_context, class_context = [], [], {}
    first_definition = next((definition_start(n) for n in tree.body if isinstance(n, DEFINITIONS)), len(lines) + 1)
    if first_definition > 1:
        module_context.append((1, first_definition - 1))
    for node in tree.body:
        cuts.add(definition_start(node))
        if not isinstance(node, DEFINITIONS):
            module_context.append((node.lineno, node.end_lineno))

    def visit(body, parents=()):
        for node in body:
            if not isinstance(node, DEFINITIONS):
                continue
            start, end = definition_start(node), node.end_lineno
            qualified = ".".join((*parents, node.name))
            symbols.append({"name": qualified, "kind": "class" if isinstance(node, ast.ClassDef) else "function", "start_line": start, "end_line": end})
            if isinstance(node, ast.ClassDef):
                first = definition_start(node.body[0])
                class_context[qualified] = [(start, max(start, first - 1))]
                class_context[qualified].extend((n.lineno, n.end_lineno) for n in node.body if not isinstance(n, DEFINITIONS))
                if not fits(start, end):
                    cuts.update(definition_start(n) for n in node.body)
                visit(node.body, (*parents, node.name))
            else:
                # Nested functions remain inside their complete outer function.
                visit(node.body, (*parents, node.name))

    visit(tree.body)
    return sorted(cuts), symbols, module_context, class_context


def chunk_file(relative: str, raw: bytes, commit: str | None, max_lines: int, max_chars: int) -> tuple[list[dict], dict]:
    text = raw.decode("utf-8")  # No newline conversion or indentation changes.
    lines = text.splitlines(keepends=True)
    digest = sha256(raw)
    inventory = {"path": relative, "sha256": digest, "bytes": len(raw), "characters": len(text), "lines": len(lines), "parse_error": None}
    if not lines:
        return [], inventory  # Empty files are recorded without inventing line 1.
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def fits(start, end):
        return end - start + 1 <= max_lines and offsets[end] - offsets[start - 1] <= max_chars

    cuts, symbols, module_context, class_context = [1, len(lines) + 1], [], [], {}
    if relative.endswith((".py", ".pyi")):
        try:
            cuts, symbols, module_context, class_context = python_structure(text, lines, fits)
        except (SyntaxError, ValueError) as error:
            inventory["parse_error"] = type(error).__name__ + ": " + str(error)

    units = []
    for start, stop in zip(cuts, cuts[1:]):
        if fits(start, stop - 1):
            units.append((start, stop - 1, False))
            continue
        # Oversized sections fall back to non-overlapping whole-line windows.
        cursor = start
        while cursor < stop:
            end = cursor
            while end + 1 < stop and fits(cursor, end + 1):
                end += 1
            units.append((cursor, end, True))
            cursor = end + 1

    spans = []
    for start, end, fallback in units:
        if spans and not fallback and not spans[-1][2] and fits(spans[-1][0], end):
            spans[-1] = (spans[-1][0], end, False)
        else:
            spans.append((start, end, fallback))

    chunks = []
    for start, end, fallback in spans:
        original = "".join(lines[start - 1:end])
        key = [VERSION, relative, digest, start, end]
        chunks.append({
            "id": sha256(dump(key).encode("utf-8")), "path": relative,
            "start_line": start, "end_line": end, "text": original,
            "source_sha256": digest, "repository_commit": commit,
            "line_count": end - start + 1, "character_count": len(original),
            "symbols": [s for s in symbols if s["start_line"] <= end and s["end_line"] >= start],
            "enclosing_classes": [s["name"] for s in symbols if s["kind"] == "class" and s["start_line"] <= end and s["end_line"] >= start],
            "line_window_fallback": fallback,
            "size_exception": "single line exceeds character limit" if len(original) > max_chars else None,
        })

    def references(ranges):
        return [c["id"] for c in chunks if any(a <= c["end_line"] and b >= c["start_line"] for a, b in ranges)]

    for chunk in chunks:
        context = set(references(module_context))
        for name in chunk["enclosing_classes"]:
            context.update(references(class_context[name]))
        chunk["context_chunk_ids"] = [c["id"] for c in chunks if c["id"] in context and c["id"] != chunk["id"]]
    return chunks, inventory


def git_value(repo: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-lines", type=int, default=120)
    parser.add_argument("--max-chars", type=int, default=6000)
    args = parser.parse_args()
    if args.max_lines < 1 or args.max_chars < 1:
        parser.error("Size limits must be positive")
    repo, output = args.repository.resolve(), args.output.resolve()
    if not repo.is_dir():
        parser.error("Repository must be a directory")
    manifest_path = output.with_suffix(".manifest.json")
    if output == manifest_path:
        parser.error("Output must not have the .manifest.json suffix")
    commit = git_value(repo, "rev-parse", "HEAD")
    candidates, excluded = source_files(repo, {output, manifest_path})
    chunks, inventory = [], []
    for path in candidates:
        relative = path.relative_to(repo).as_posix()
        raw = path.read_bytes()
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            excluded.append({"path": relative, "reason": "not UTF-8 text"})
            continue
        if any(ord(c) < 32 and c not in "\t\r\n" for c in decoded):
            excluded.append({"path": relative, "reason": "binary/control characters"})
            continue
        file_chunks, entry = chunk_file(relative, raw, commit, args.max_lines, args.max_chars)
        chunks.extend(file_chunks)
        inventory.append(entry)
    payload = "".join(dump(chunk) + "\n" for chunk in chunks).encode("utf-8")
    manifest = {
        "schema_version": VERSION, "repository_commit": commit,
        "git_status_porcelain": git_value(repo, "status", "--porcelain=v1", "--untracked-files=no"),
        "limits": {"max_lines": args.max_lines, "max_characters": args.max_chars, "overlap_lines": 0},
        "files": inventory, "excluded": sorted(excluded, key=lambda e: e["path"]),
        "file_count": len(inventory), "chunk_count": len(chunks), "chunks_sha256": sha256(payload),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(dump({"files": len(inventory), "chunks": len(chunks), "chunks_sha256": sha256(payload)}))


if __name__ == "__main__":
    main()
