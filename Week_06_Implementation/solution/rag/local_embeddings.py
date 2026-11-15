"""Shared CPU encoder with explicit, lossless token-window coverage.

No inference API is used. Hugging Face is contacted only to resolve/download
public model files unless local_files_only=True with a pinned revision.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from huggingface_hub import HfApi, snapshot_download
import numpy as np
from sentence_transformers import SentenceTransformer
import torch


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
REPRESENTATION = "path-classes-first6-symbols-original-source-v1"
AGGREGATION = "payload-token-count-weighted mean of L2-normalized window vectors, then L2 normalization"


def chunk_prefix(chunk: dict) -> str:
    """Keep metadata concise; full definitions remain in original source text."""
    classes = list(dict.fromkeys(chunk.get("enclosing_classes", [])))
    symbols = list(dict.fromkeys(s["name"] for s in chunk.get("symbols", []) if s["kind"] != "class"))
    selected = ", ".join(symbols[:6]) or "(none)"
    if len(symbols) > 6:
        selected += f" (+{len(symbols) - 6} more in source)"
    return (
        f'Path: {chunk["path"]} (lines {chunk["start_line"]}-{chunk["end_line"]})\n'
        f'Classes: {", ".join(classes) or "(none)"}\n'
        f"Symbols: {selected}\n\nSource:\n"
    )


def chunk_text(chunk: dict) -> str:
    return chunk_prefix(chunk) + chunk["text"]


def token_windows(length: int, capacity: int, overlap: int) -> list[tuple[int, int]]:
    """Half-open payload-token ranges. Last window ends at the final token."""
    if length < 1 or capacity < 1 or not 0 <= overlap < capacity:
        raise ValueError("Need nonempty input, positive capacity, and 0 <= overlap < capacity")
    windows = []
    start = 0
    while start < length:
        end = min(length, start + capacity)
        windows.append((start, end))
        if end == length:
            break
        start = end - overlap
    return windows


class TextEncoder:
    """Reuse this class for query text with the recorded model and processing."""

    def __init__(self, model_id=MODEL_ID, revision="main", cache_dir=None,
                 overlap=32, batch_size=16, threads=2, local_files_only=False):
        if batch_size < 1 or threads < 1:
            raise ValueError("batch_size and threads must be positive")
        if re.fullmatch(r"[0-9a-f]{40}", revision):
            resolved = revision
        elif local_files_only:
            raise ValueError("Offline loading requires the resolved 40-character model revision")
        else:
            resolved = HfApi(token=False).model_info(model_id, revision=revision).sha
        self.model_id, self.revision = model_id, resolved
        self.overlap, self.batch_size, self.threads = overlap, batch_size, threads
        snapshot = snapshot_download(
            model_id, revision=resolved, cache_dir=cache_dir, token=False,
            local_files_only=local_files_only, max_workers=2,
            allow_patterns=["*.json", "*.txt", "model.safetensors"],
        )
        torch.set_num_threads(threads)
        torch.use_deterministic_algorithms(True)
        self.model = SentenceTransformer(
            snapshot, device="cpu", local_files_only=True, trust_remote_code=False,
            model_kwargs={"attn_implementation": "eager"},
        ).float().eval()
        self.tokenizer = self.model.tokenizer
        limits = {
            "tokenizer_config_model_max_length": int(json.loads((Path(snapshot) / "tokenizer_config.json").read_text())["model_max_length"]),
            "sentence_transformer_max_seq_length": int(self.model.max_seq_length),
            "tokenizer_model_max_length": int(self.tokenizer.model_max_length),
            "transformer_max_position_embeddings": int(self.model[0].auto_model.config.max_position_embeddings),
        }
        self.limit = min(limits.values())
        self.special_tokens = self.tokenizer.num_special_tokens_to_add(pair=False)
        self.capacity = self.limit - self.special_tokens
        if self.capacity < 1 or not 0 <= overlap < self.capacity:
            raise ValueError("Overlap must be smaller than the supported payload capacity")
        self.dimensions = self.model.get_sentence_embedding_dimension()
        if self.dimensions != 384:
            raise ValueError(f"Unexpected model dimensions: {self.dimensions}")
        self.limits = {
            **limits, "effective_input_tokens": self.limit,
            "special_tokens_per_window": self.special_tokens,
            "payload_tokens_per_window": self.capacity,
        }

    def tokenize(self, text: str) -> list[int]:
        # No model call and no truncation; warnings about full-text length would
        # be misleading because only bounded token windows enter the model.
        return self.tokenizer(
            text, add_special_tokens=False, truncation=False,
            return_attention_mask=False, return_token_type_ids=False, verbose=False,
        )["input_ids"]

    def plan(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        ids = self.tokenize(text)
        return ids, token_windows(len(ids), self.capacity, self.overlap)

    def encode_texts(self, texts: list[str]) -> tuple[np.ndarray, list[dict]]:
        """Return one float32 unit vector per text and auditable window plans.

        Token IDs go straight to model.forward, without decode/re-tokenize or
        SentenceTransformer.encode's implicit text truncation. Overlap tokens
        participate in both windows intentionally. Each window is weighted by
        its payload length, so a short final window has proportionally less weight.
        """
        if not texts:
            raise ValueError("At least one text is required")
        prepared, owners, lengths, details = [], [], [], []
        for row, text in enumerate(texts):
            ids, windows = self.plan(text)
            coverage = np.zeros(len(ids), dtype=np.int32)
            for start, end in windows:
                payload = ids[start:end]
                features = self.tokenizer.prepare_for_model(
                    payload, add_special_tokens=True, truncation=False,
                    return_attention_mask=True, return_token_type_ids=True,
                )
                if features["input_ids"] != self.tokenizer.build_inputs_with_special_tokens(payload):
                    raise ValueError("Token preparation changed payload IDs")
                if len(features["input_ids"]) != end - start + self.special_tokens or len(features["input_ids"]) > self.limit:
                    raise ValueError("Prepared window exceeds the effective model limit")
                coverage[start:end] += 1
                prepared.append(features)
                owners.append(row)
                lengths.append(end - start)
            if not np.all(coverage > 0):
                raise ValueError("Window plan omitted input tokens")
            details.append({
                "input_tokens_without_special": len(ids),
                "input_tokens_with_special_if_unsplit": len(ids) + self.special_tokens,
                "window_token_ranges": [list(w) for w in windows],
                "window_model_input_tokens": [end - start + self.special_tokens for start, end in windows],
                "window_weights_payload_tokens": [end - start for start, end in windows],
                "window_count": len(windows), "full_token_coverage": True,
            })

        sums = np.zeros((len(texts), self.dimensions), dtype=np.float64)
        weights = np.zeros(len(texts), dtype=np.float64)
        for start in range(0, len(prepared), self.batch_size):
            features = self.tokenizer.pad(prepared[start:start + self.batch_size], padding=True, return_tensors="pt")
            if features["input_ids"].shape[1] > self.limit:
                raise ValueError("Padded batch exceeds model limit")
            with torch.inference_mode():
                vectors = self.model(features)["sentence_embedding"]
                vectors = torch.nn.functional.normalize(vectors, p=2, dim=1).cpu().numpy()
            if not np.isfinite(vectors).all() or np.any(np.linalg.norm(vectors, axis=1) < 1e-8):
                raise ValueError("Invalid window vector")
            for offset, vector in enumerate(vectors):
                index = start + offset
                sums[owners[index]] += vector.astype(np.float64) * lengths[index]
                weights[owners[index]] += lengths[index]
        means = sums / weights[:, None]
        norms = np.linalg.norm(means, axis=1, keepdims=True)
        if not np.isfinite(means).all() or np.any(norms < 1e-8):
            raise ValueError("Invalid aggregate vector")
        return (means / norms).astype(np.float32), details

    def settings(self) -> dict:
        return {
            "limits": self.limits, "overlap_payload_tokens": self.overlap,
            "stride_payload_tokens": self.capacity - self.overlap,
            "aggregation": AGGREGATION, "normalization": "L2, per window and after aggregation",
            "batch_size": self.batch_size, "cpu_threads": self.threads,
            "device": "cpu", "attention_implementation": "eager",
            "deterministic_algorithms": True,
        }

    @classmethod
    def from_metadata(cls, metadata_path, cache_dir=None, local_files_only=True):
        """Load the pinned encoder for Task 4; query text needs no code prefix."""
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        settings, model = metadata["encoding"], metadata["model"]
        encoder = cls(
            model_id=model["identifier"], revision=model["resolved_revision"],
            cache_dir=cache_dir, overlap=settings["overlap_payload_tokens"],
            batch_size=settings["batch_size"], threads=settings["cpu_threads"],
            local_files_only=local_files_only,
        )
        if encoder.settings() != settings:
            raise ValueError("Current encoder settings differ from the stored corpus settings")
        return encoder
