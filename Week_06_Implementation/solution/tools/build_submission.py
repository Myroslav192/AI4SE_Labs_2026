#!/usr/bin/env python3
"""Copy ordinary submission files into a ZIP; never alter the live nested Git repo."""

import argparse
import hashlib
import os
from pathlib import Path
import stat
import zipfile


EXCLUDED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "env", ".cache", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".safetensors", ".pt", ".pth", ".onnx", ".bin", ".pem", ".key", ".p12", ".pfx", ".zip", ".tmp"}


def selected_files(root):
    paths = [root / name for name in ("SUBMISSION.md", ".env.example", ".gitignore")]
    for name in ("Assignments", "solution"):
        for directory, dirs, files in os.walk(root / name, followlinks=False):
            parent = Path(directory)
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not (parent / d).is_symlink())
            for filename in sorted(files):
                path = parent / filename
                if path.is_symlink():
                    raise ValueError("Submission payload must contain ordinary files, not symlinks")
                if filename.startswith(".env") or filename.lower().startswith(("credentials", "secrets")) or path.suffix.lower() in EXCLUDED_SUFFIXES:
                    continue
                paths.append(path)
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "Week06_RAG_submission.zip").resolve()
    files = selected_files(root)
    if any(not path.is_file() for path in files):
        parser.error("Required submission documentation/configuration is missing")
    if not (root / "solution/reports/package_verification.md").is_file():
        parser.error("Write package_verification.md before finalizing the archive")
    manifest = "".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.relative_to(root).as_posix() + "\n" for p in files)
    (root / "SHA256SUMS").write_text(manifest, encoding="utf-8")
    files.append(root / "SHA256SUMS")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(2026, 11, 15, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(digest + "  " + output.name + "\n")
    print(f"Archive files: {len(files)}; manifest entries: {len(files)-1}; bytes: {output.stat().st_size}; SHA-256: {digest}")


if __name__ == "__main__":
    main()
