"""Deterministic recursive loading, MIME decoding, chunking and evidence checks."""
import hashlib
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path

from .schemas import Candidate, CandidateText, Chunk, Document

SUPPORTED = {".txt", ".md", ".eml"}


def decode_text(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def read_email(raw: bytes) -> str:
    message = BytesParser(policy=policy.default).parsebytes(raw)
    headers = "\n".join(f"{key}: {message[key]}" for key in ("From", "To", "Cc", "Subject", "Date") if message[key])
    if message.is_multipart():
        parts = [part.get_content() for part in message.walk()
                 if part.get_content_type() == "text/plain" and part.get_content_disposition() != "attachment"]
        if not parts:
            raise ValueError("Email contains no plain-text body; convert HTML-only messages to text first.")
        body = "\n\n".join(parts)
    else:
        if message.get_content_type() != "text/plain":
            raise ValueError("Only plain-text email bodies are supported.")
        charset = message.get_content_charset()
        payload = message.get_payload(decode=True) or b""
        body = payload.decode(charset) if charset else decode_text(payload)
    return headers + "\n\n" + body


def load_corpus(directory: Path) -> tuple[list[Document], list[str]]:
    root = directory.resolve()
    if not root.is_dir():
        raise ValueError(f"Input directory does not exist: {directory}")
    documents, skipped = [], []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Input symlink is not supported: {relative}")
        if path.suffix.lower() not in SUPPORTED:
            skipped.append(relative)
            continue
        raw = path.read_bytes()
        try:
            text = read_email(raw) if path.suffix.lower() == ".eml" else decode_text(raw)
        except (UnicodeError, LookupError, ValueError) as exc:
            raise ValueError(f"Cannot read {relative}: {exc}") from exc
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            raise ValueError(f"Empty input document: {relative}")
        documents.append(Document(id=f"DOC-{len(documents) + 1:03d}", path=relative,
                                  sha256=hashlib.sha256(raw).hexdigest(), text=text))
    if not documents:
        raise ValueError("No supported .txt, .md or .eml documents were found.")
    return documents, skipped


def chunk_documents(documents: list[Document], max_chars: int = 12000, overlap_lines: int = 8) -> list[Chunk]:
    if max_chars < 500 or overlap_lines < 0:
        raise ValueError("Chunk size must be >= 500 and overlap must be nonnegative.")
    chunks = []
    for document in documents:
        lines, start, number = document.text.splitlines(), 0, 1
        while start < len(lines):
            end, size = start, 0
            while end < len(lines) and (end == start or size + len(lines[end]) + 1 <= max_chars):
                size += len(lines[end]) + 1
                end += 1
            chunks.append(Chunk(id=f"{document.id}-CH-{number:03d}", document_id=document.id,
                                start_line=start + 1, end_line=end, text="\n".join(lines[start:end])))
            if end == len(lines):
                break
            start = max(start + 1, end - overlap_lines)
            number += 1
    return chunks


def normalize(text: str) -> str:
    return " ".join(text.split())


def ground_candidate(item: CandidateText, document: Document, chunk: Chunk, candidate_id: str) -> Candidate:
    # Quotes must match source text after whitespace normalization. Approximate or
    # invented quotations never silently become accepted provenance.
    quote = normalize(item.evidence_quote)
    if len(quote) < 3:
        raise ValueError("Evidence quotation is empty or too short to locate.")
    compact, line_numbers = [], []
    for number, line in enumerate(chunk.text.splitlines(), chunk.start_line):
        for word in re.findall(r"\S+", line):
            if compact:
                compact.append(" ")
                line_numbers.append(number)
            compact.extend(word)
            line_numbers.extend([number] * len(word))
    source = "".join(compact)
    # Small models sometimes capitalize a mid-sentence quotation or append a
    # sentence period to a bullet. Repair ONLY those presentation differences,
    # then save the actual source substring, never a guessed/paraphrased quote.
    variants = [quote]
    quote_marks = "\"'“”‘’"
    if len(quote) > 2 and quote[0] in quote_marks and quote[-1] in quote_marks:
        variants.append(quote[1:-1])
    variants += [value[:-1] for value in list(variants) if value.endswith(".") and not value.endswith("...")]
    match = None
    for variant in variants:
        pattern = "".join("[\"'“”‘’]" if char in quote_marks else re.escape(char) for char in variant)
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if match:
            break
    if match is None:
        raise ValueError(f"Evidence for {item.name!r} does not occur in {chunk.id}: {item.evidence_quote!r}")
    fields = item.model_dump()
    fields["evidence_quote"] = source[match.start():match.end()]
    return Candidate(**fields, id=candidate_id, document_id=document.id, chunk_id=chunk.id,
                     start_line=line_numbers[match.start()], end_line=line_numbers[match.end() - 1])
