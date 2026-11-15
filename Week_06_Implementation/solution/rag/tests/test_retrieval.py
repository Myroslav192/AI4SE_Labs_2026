"""Ranking, validation, real-query, and saved-evaluation checks for Task 4."""

import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retrieve_chunks import ArtifactError, ChunkRetriever, build_task_query, rank_vectors, retrieve_chunks


ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "solution/artifacts"


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.vectors = np.array([[1, 0], [1, 0], [0, 1], [-1, 0]], dtype=np.float64)
        self.ids = np.array(["b", "a", "c", "d"])

    def test_independent_cosines_and_tie_breaker(self):
        query = [3, 4]
        # Plain Python scalar arithmetic, independently of NumPy ranking.
        norm = math.sqrt(sum(x * x for x in query))
        expected_scores = [sum(float(x) * y for x, y in zip(row, query)) / norm for row in self.vectors]
        expected_order = sorted(range(4), key=lambda i: (-expected_scores[i], self.ids[i]))
        order, scores = rank_vectors(self.vectors, self.ids, query, 4)
        self.assertEqual(order.tolist(), expected_order)
        self.assertEqual(self.ids[order].tolist(), ["c", "a", "b", "d"])
        np.testing.assert_allclose(scores, [0.6, 0.6, 0.8, -0.6], rtol=0, atol=1e-15)
        order2, _ = rank_vectors(self.vectors[::-1], self.ids[::-1], query, 4)
        self.assertEqual(self.ids[::-1][order2].tolist(), ["c", "a", "b", "d"])

    def test_positive_n_distinctness_and_large_n(self):
        for invalid in [0, -1, True, False, 1.5, "5", None, float("nan")]:
            with self.subTest(n=invalid), self.assertRaisesRegex(ValueError, "positive integer"):
                rank_vectors(self.vectors, self.ids, [3, 4], invalid)
        order, _ = rank_vectors(self.vectors, self.ids, [3, 4], 999)
        self.assertEqual(len(order), 4)
        self.assertEqual(len(set(self.ids[order])), 4)
        order, _ = rank_vectors(self.vectors, self.ids, [3, 4], 1)
        self.assertEqual(self.ids[order].tolist(), ["c"])

    def test_invalid_vectors_and_duplicate_ids(self):
        for query in [[0, 0], [float("nan"), 1], [float("inf"), 1], [1, 0, 0]]:
            with self.subTest(query=query), self.assertRaises(ValueError):
                rank_vectors(self.vectors, self.ids, query, 2)
        with self.assertRaisesRegex(ValueError, "distinct"):
            rank_vectors(self.vectors, np.array(["a", "a", "b", "c"]), [3, 4], 2)
        with self.assertRaisesRegex(ValueError, "unit vectors"):
            rank_vectors(self.vectors * 2, self.ids, [3, 4], 2)


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = ChunkRetriever(
            ARTIFACTS / "chunks.jsonl", ARTIFACTS / "embeddings.npz", ARTIFACTS / "embeddings.metadata.json",
            cache_dir=ROOT / ".cache/huggingface",
        )

    def test_real_cli_results_match_function_and_scalar_scores(self):
        example = json.loads((ARTIFACTS / "task4_cli_example.json").read_bytes())
        results = self.retriever.search(example["query"], 5)
        self.assertEqual([r["chunk_id"] for r in results], [r["chunk_id"] for r in example["results"]])
        np.testing.assert_allclose([r["score"] for r in results], [r["score"] for r in example["results"]], rtol=1e-5, atol=1e-6)
        vector, _ = self.retriever.encoder.encode_texts([example["query"]])
        query = [float(v) for v in vector[0]]
        norm = math.sqrt(math.fsum(v * v for v in query))
        scalar_scores = [math.fsum(float(x) * y / norm for x, y in zip(row, query)) for row in self.retriever.vectors]
        expected = sorted(range(len(scalar_scores)), key=lambda i: (-scalar_scores[i], self.retriever.ids[i]))[:5]
        self.assertEqual([r["chunk_id"] for r in results], self.retriever.ids[expected].tolist())
        np.testing.assert_allclose([r["score"] for r in results], [scalar_scores[i] for i in expected], rtol=0, atol=1e-12)
        for result in results:
            original = next(c for c in self.retriever.chunks if c["id"] == result["chunk_id"])
            for key in ("path", "start_line", "end_line", "symbols", "enclosing_classes", "text"):
                self.assertEqual(result[key], original[key])

    def test_repeated_search_large_n_and_invalid_arguments(self):
        first = self.retriever.search("Inventory stock and reservation", 100)
        second = self.retriever.search("Inventory stock and reservation", 100)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 55)
        self.assertEqual(len({r["chunk_id"] for r in first}), 55)
        self.assertEqual([(-r["score"], r["chunk_id"]) for r in first], sorted((-r["score"], r["chunk_id"]) for r in first))
        with patch.object(self.retriever.encoder, "encode_texts", side_effect=AssertionError("Must validate first")):
            for invalid in [0, -1, True, 2.5, "5"]:
                with self.assertRaises(ValueError):
                    self.retriever.search("inventory", invalid)
            for invalid in ["", "   ", None, 42]:
                with self.assertRaises(ValueError):
                    self.retriever.search(invalid, 5)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            retrieve_chunks("query", 0, chunks_path="missing", embeddings_path="missing", metadata_path="missing")

    def test_long_query_uses_compatible_complete_windows(self):
        query = "Inventory balance customer order status. " * 100
        results = self.retriever.search(query, 3)
        plan = self.retriever.last_query_encoding
        self.assertEqual(len(results), 3)
        self.assertGreater(plan["window_count"], 1)
        self.assertTrue(plan["full_token_coverage"])
        self.assertEqual(plan["window_token_ranges"][-1][1], len(self.retriever.encoder.tokenize(query)))
        self.assertLessEqual(max(plan["window_model_input_tokens"]), 256)
        self.assertEqual(self.retriever.encoder.settings(), self.retriever.metadata["encoding"])

    def test_corrupt_and_incompatible_artifacts_fail_before_model_loading(self):
        original = self.retriever.metadata
        with tempfile.TemporaryDirectory(prefix="week06-retrieval-check-") as tmp:
            root = Path(tmp)
            meta_path = root / "metadata.json"
            npz = root / "vectors.npz"
            chunks = root / "chunks.jsonl"

            def check(metadata, chunk_path=ARTIFACTS / "chunks.jsonl", npz_path=ARTIFACTS / "embeddings.npz"):
                meta_path.write_text(json.dumps(metadata))
                with patch("retrieve_chunks.TextEncoder.from_metadata", side_effect=AssertionError("Invalid artifacts must fail first")):
                    with self.assertRaisesRegex(ArtifactError, "retrieval artifacts"):
                        ChunkRetriever(chunk_path, npz_path, meta_path, source_manifest=ARTIFACTS / "chunks.manifest.json")

            bad = deepcopy(original)
            bad["encoding"]["normalization"] = "none"
            check(bad)
            bad = deepcopy(original)
            bad["model"]["dimensions"] = 128
            check(bad)
            bad = deepcopy(original)
            bad["rows"][0]["chunk_id"] = "wrong"
            check(bad)
            chunks.write_bytes((ARTIFACTS / "chunks.jsonl").read_bytes() + b"\n")
            check(original, chunk_path=chunks)
            np.savez_compressed(npz, embeddings=self.retriever.vectors[::-1], chunk_ids=self.retriever.ids[::-1])
            bad = deepcopy(original)
            bad["storage"]["npz_sha256"] = hashlib.sha256(npz.read_bytes()).hexdigest()
            check(bad, npz_path=npz)
            npz.write_bytes(b"PK\x03\x04\x00\x00")
            bad["storage"]["npz_sha256"] = hashlib.sha256(npz.read_bytes()).hexdigest()
            check(bad, npz_path=npz)
            check(original, npz_path=root / "absent.npz")

    def test_saved_evaluation_queries_rankings_and_original_target_spans(self):
        evaluation = json.loads((ARTIFACTS / "retrieval_evaluation.json").read_bytes())
        tasks = json.loads((ROOT.parent / "missing_code.json").read_bytes())
        self.assertEqual(len(evaluation["tasks"]), len(tasks))
        observed_hits = 0
        for task, row in zip(tasks, evaluation["tasks"]):
            self.assertEqual(row["task"], task)
            self.assertEqual(row["query"], build_task_query(task))
            self.assertEqual(len(row["results"]), 5)
            self.assertEqual(len({r["chunk_id"] for r in row["results"]}), 5)
            actual = self.retriever.search(row["query"], 5)
            self.assertEqual([r["chunk_id"] for r in actual], [r["chunk_id"] for r in row["results"]])
            tree = ast.parse((ROOT / "solution/AI4SE_Playground" / task["file"]).read_bytes())
            cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == task["class"])
            method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == task["method"])
            start = min([method.lineno] + [d.lineno for d in method.decorator_list])
            self.assertEqual((row["target_span"]["start_line"], row["target_span"]["end_line"]), (start, method.end_lineno))
            hit = any(r["path"] == task["file"] and r["start_line"] <= start and r["end_line"] >= method.end_lineno for r in actual)
            self.assertEqual(hit, row["target_method_hit"])
            observed_hits += hit
        self.assertEqual(observed_hits, evaluation["summary"]["target_method_hits_at_5"])

    def test_task_query_builder_preserves_supplied_behavior(self):
        task = {"file": "example.py", "class": "Example", "method": "method", "docstring": '    """Return the supplied value."""'}
        self.assertEqual(build_task_query(task), "Implement Example.method in example.py.\nRequired behavior: Return the supplied value.")
        with self.assertRaises(ValueError):
            build_task_query({"file": "example.py"})


if __name__ == "__main__":
    unittest.main()
