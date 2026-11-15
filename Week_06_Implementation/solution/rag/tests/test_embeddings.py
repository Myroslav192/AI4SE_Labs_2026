"""Real-model integration checks; generate embeddings before running these tests.

From the assignment directory:
HF_HUB_OFFLINE=1 .venv/bin/python -m unittest discover -s solution/rag/tests -v
"""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from embed_repository import load_embedding_store
from local_embeddings import TextEncoder, chunk_text, token_windows


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "solution/artifacts"


class EmbeddingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata_path = ARTIFACTS / "embeddings.metadata.json"
        cls.matrix, cls.ids, cls.metadata = load_embedding_store(
            ARTIFACTS / "embeddings.npz", cls.metadata_path, ARTIFACTS / "chunks.jsonl",
        )
        cls.chunks = [json.loads(line) for line in (ARTIFACTS / "chunks.jsonl").read_bytes().splitlines()]
        cls.encoder = TextEncoder.from_metadata(cls.metadata_path, cache_dir=ROOT / ".cache/huggingface")

    def test_actual_storage_and_provenance(self):
        self.assertEqual(self.matrix.shape, (55, 384))
        self.assertEqual(self.matrix.dtype, np.float32)
        self.assertEqual(self.ids.dtype.kind, "U")
        self.assertEqual(self.ids.tolist(), [c["id"] for c in self.chunks])
        self.assertEqual(len(set(self.ids)), 55)
        self.assertTrue(np.isfinite(self.matrix).all())
        np.testing.assert_allclose(np.linalg.norm(self.matrix, axis=1), 1, rtol=0, atol=1e-5)
        source = self.metadata["source"]
        manifest = ARTIFACTS / source["manifest_path"]
        self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(), source["manifest_sha256"])

    def test_every_actual_token_is_covered_with_bounded_windows(self):
        encoder = self.encoder
        for chunk, row in zip(self.chunks, self.metadata["rows"]):
            with self.subTest(chunk_id=chunk["id"]):
                text = chunk_text(chunk)
                self.assertTrue(text.endswith(chunk["text"]))
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), row["embedding_text_sha256"])
                ids = encoder.tokenize(text)
                self.assertEqual(len(ids), row["input_tokens_without_special"])
                coverage = np.zeros(len(ids), dtype=int)
                previous_end = None
                for start, end in row["window_token_ranges"]:
                    self.assertGreater(end, start)
                    if previous_end is None:
                        self.assertEqual(start, 0)
                    else:
                        self.assertEqual(start, previous_end - encoder.overlap)
                    prepared = encoder.tokenizer.build_inputs_with_special_tokens(ids[start:end])
                    self.assertEqual(len(prepared), end - start + encoder.special_tokens)
                    self.assertLessEqual(len(prepared), encoder.limit)
                    coverage[start:end] += 1
                    previous_end = end
                self.assertEqual(previous_end, len(ids))
                self.assertTrue((coverage > 0).all())
                self.assertEqual(row["window_count"], len(row["window_token_ranges"]))

    def test_window_boundary_cases_and_invalid_inputs(self):
        for length in [1, 253, 254, 255, 476, 477, 1000]:
            with self.subTest(length=length):
                windows = token_windows(length, 254, 32)
                self.assertEqual(windows[0][0], 0)
                self.assertEqual(windows[-1][1], length)
                self.assertEqual(set(i for a, b in windows for i in range(a, b)), set(range(length)))
                self.assertTrue(all(b - a <= 254 for a, b in windows))
        for arguments in [(0, 254, 32), (1, 0, 0), (1, 254, 254), (1, 254, -1)]:
            with self.assertRaises(ValueError):
                token_windows(*arguments)
        with self.assertRaises(ValueError):
            self.encoder.encode_texts([""])

    def test_pinned_cpu_query_encoder_matches_standard_short_encoding(self):
        text = "Which order statuses prevent further transitions?"
        custom, plans = self.encoder.encode_texts([text])
        reference = self.encoder.model.encode([text], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        np.testing.assert_allclose(custom, reference, atol=1e-6, rtol=1e-5)
        self.assertEqual(plans[0]["window_count"], 1)
        self.assertEqual(self.encoder.revision, self.metadata["model"]["resolved_revision"])
        self.assertEqual(str(self.encoder.model.device), "cpu")
        self.assertIsNone(torch.version.cuda)

    def test_long_actual_chunk_matches_independent_window_aggregation(self):
        row = max(self.metadata["rows"], key=lambda r: r["input_tokens_without_special"])
        index = row["row"]
        token_ids = self.encoder.tokenize(chunk_text(self.chunks[index]))
        vectors, weights = [], []
        for start, end in row["window_token_ranges"]:
            ids = self.encoder.tokenizer.build_inputs_with_special_tokens(token_ids[start:end])
            inputs = {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones((1, len(ids)), dtype=torch.long)}
            with torch.inference_mode():
                vector = self.encoder.model(inputs)["sentence_embedding"].numpy()[0]
            vectors.append(vector.astype(np.float64) / np.linalg.norm(vector))
            weights.append(end - start)
        self.assertGreater(len(vectors), 1)
        expected = np.average(vectors, axis=0, weights=weights)
        expected /= np.linalg.norm(expected)
        np.testing.assert_allclose(self.matrix[index], expected, rtol=1e-5, atol=1e-6)
        self.assertFalse(np.allclose(self.matrix[index], vectors[0], atol=1e-4, rtol=1e-4))

    def test_loader_rejects_mismatched_chunks_and_storage(self):
        with tempfile.TemporaryDirectory(prefix="week06-embedding-check-") as tmp:
            altered = Path(tmp) / "chunks.jsonl"
            altered.write_bytes((ARTIFACTS / "chunks.jsonl").read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "Chunk JSONL"):
                load_embedding_store(ARTIFACTS / "embeddings.npz", self.metadata_path, altered)
            npz = Path(tmp) / "embeddings.npz"
            npz.write_bytes((ARTIFACTS / "embeddings.npz").read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "NPZ"):
                load_embedding_store(npz, self.metadata_path, ARTIFACTS / "chunks.jsonl")


if __name__ == "__main__":
    unittest.main()
