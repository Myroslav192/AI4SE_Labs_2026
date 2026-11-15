"""Validate a model-returned method and atomically replace only its body.

Parsing and compilation are structural checks; returned code is never executed
to perform editing. These checks do not establish functional correctness.
"""

import ast
from copy import deepcopy
from dataclasses import dataclass
import difflib
import io
import os
from pathlib import Path
import stat
import tempfile
import tokenize


class ValidationError(ValueError):
    pass


def resolve_target(repository, relative):
    root = Path(repository).resolve()
    relative = Path(relative)
    if relative.is_absolute() or relative.suffix != ".py":
        raise ValidationError("Target must be a repository-relative Python file")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or ".git" in relative.parts:
        raise ValidationError("Target path escapes the configured source repository")
    if not path.is_file():
        raise ValidationError("Target source file does not exist")
    return path


def locate(tree, target):
    scope = tree
    for name in target["class"].split("."):
        matches = [n for n in scope.body if isinstance(n, ast.ClassDef) and n.name == name]
        if len(matches) != 1:
            raise ValidationError("Target class must resolve uniquely")
        scope = matches[0]
    methods = [n for n in scope.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == target["method"]]
    if len(methods) != 1:
        raise ValidationError("Target method must resolve uniquely in its class")
    return methods[0]


def offsets(raw):
    lines = raw.splitlines(keepends=True)
    positions = [0]
    for line in lines:
        positions.append(positions[-1] + len(line))
    return lines, positions


def statement_start(node):
    decorators = getattr(node, "decorator_list", [])
    return min([node.lineno] + [d.lineno for d in decorators])


def without_docstring(node):
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def signature(node):
    fields = (node.args, node.returns, node.decorator_list, getattr(node, "type_params", []), node.type_comment)
    return (type(node).__name__, node.name, [ast.dump(v, include_attributes=False) if isinstance(v, ast.AST) else repr([ast.dump(x) for x in v]) if isinstance(v, list) else v for v in fields])


@dataclass
class Edit:
    path: Path
    before: bytes
    after: bytes
    diff: str


def current_method(repository, target):
    path = resolve_target(repository, target["file"])
    raw = path.read_bytes()
    tree = ast.parse(raw, type_comments=True)
    method = locate(tree, target)
    lines, positions = offsets(raw)
    start = statement_start(method)
    snippet = raw[positions[start - 1]:positions[method.end_lineno]].decode("utf-8")
    return snippet


def prepare_edit(repository, target, returned_code):
    if not isinstance(returned_code, str) or not returned_code.strip():
        raise ValidationError("Response contains no method code")
    path = resolve_target(repository, target["file"])
    before = path.read_bytes()
    old_tree = ast.parse(before, type_comments=True)
    old = locate(old_tree, target)  # Always recompute after earlier file edits.
    try:
        returned = ast.parse(returned_code, type_comments=True)
    except SyntaxError as error:
        raise ValidationError("Response is not a standalone Python method definition") from error
    if len(returned.body) != 1 or not isinstance(returned.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValidationError("Response must contain exactly one method, with no unrelated definitions/imports")
    new = returned.body[0]
    if signature(old) != signature(new):
        raise ValidationError("Method name, signature, decorators, or annotations differ from the target")
    if ast.get_docstring(old, clean=False) != ast.get_docstring(new, clean=False):
        raise ValidationError("Existing docstring must be preserved; do not add a new docstring")
    body = without_docstring(new)
    old_body = without_docstring(old)
    if not body or not old_body:
        raise ValidationError("Expected an existing replaceable body and a nonempty generated body")
    for node in ast.walk(new):
        if isinstance(node, ast.Pass) or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
            raise ValidationError("Placeholder pass/ellipsis is not a complete implementation")
        if isinstance(node, ast.Raise) and node.exc is not None:
            exception = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            if isinstance(exception, ast.Name) and exception.id == "NotImplementedError":
                raise ValidationError("NotImplementedError placeholder is not accepted")
    try:
        compile(returned, "<model-method>", "exec", dont_inherit=True)
    except SyntaxError as error:
        raise ValidationError("Returned method fails Python compilation") from error
    if [ast.dump(n) for n in body] == [ast.dump(n) for n in old_body]:
        raise ValidationError("Returned implementation does not change the existing body")

    old_lines, old_positions = offsets(before)
    generated = returned_code.encode("utf-8")
    new_lines, new_positions = offsets(generated)
    old_first, new_first = old_body[0], body[0]
    old_line, new_line = statement_start(old_first), statement_start(new_first)
    if old_line == old.lineno or new_line == new.lineno:
        raise ValidationError("Inline one-line method bodies are not supported")
    old_indent = old_lines[old_line - 1][:old_first.col_offset]
    new_indent = new_lines[new_line - 1][:new_first.col_offset]
    if old_indent.strip() or new_indent.strip() or not new_indent:
        raise ValidationError("Unsupported body indentation")
    # Keep continuation lines inside multiline string literals unchanged so
    # moving the method into a class does not alter literal string values.
    string_continuations = set()
    for token in tokenize.tokenize(io.BytesIO(generated).readline):
        if token.type == tokenize.STRING and token.end[0] > token.start[0]:
            string_continuations.update(range(token.start[0] + 1, token.end[0] + 1))
    adjusted = []
    for number in range(new_line, new.end_lineno + 1):
        line = new_lines[number - 1]
        if number == new.end_lineno:
            line = line[:new.end_col_offset]
        if number not in string_continuations and line.startswith(new_indent):
            line = old_indent + line[len(new_indent):]
        adjusted.append(line)
    replacement = b"".join(adjusted)[len(old_indent):]
    start = old_positions[old_line - 1] + old_first.col_offset
    end = old_positions[old.end_lineno - 1] + old.end_col_offset
    after = before[:start] + replacement + before[end:]
    try:
        new_tree = ast.parse(after, type_comments=True)
        compile(new_tree, str(path), "exec", dont_inherit=True)
    except SyntaxError as error:
        raise ValidationError("Complete patched source file fails Python compilation") from error
    patched = locate(new_tree, target)
    if [ast.dump(n) for n in without_docstring(patched)] != [ast.dump(n) for n in body]:
        raise ValidationError("Indentation conversion changed the generated body syntax or literal values")
    if ast.get_docstring(patched, clean=False) != ast.get_docstring(old, clean=False):
        raise ValidationError("Patching changed the original docstring")
    restored = deepcopy(new_tree)
    locate(restored, target).body = deepcopy(old.body)
    if ast.dump(restored) != ast.dump(old_tree):
        raise ValidationError("Patched file changes syntax outside the target method body")
    diff = "".join(difflib.unified_diff(before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True), fromfile="a/" + target["file"], tofile="b/" + target["file"]))
    return Edit(path, before, after, diff)


def apply_edit(edit, backup_path):
    if edit.path.read_bytes() != edit.before:
        raise ValidationError("Source changed concurrently; refusing to overwrite it")
    backup_path = Path(backup_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        if backup_path.read_bytes() != edit.before:
            raise ValidationError("Recovery backup already exists with different contents")
    else:
        with backup_path.open("xb") as handle:
            handle.write(edit.before)
    mode = stat.S_IMODE(edit.path.stat().st_mode)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=edit.path.parent, prefix=".rag-method-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(edit.after)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        if edit.path.read_bytes() != edit.before:
            raise ValidationError("Source changed before atomic replacement")
        os.replace(temporary, edit.path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
