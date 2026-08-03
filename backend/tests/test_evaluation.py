import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from app.evaluation.retrieval_metrics import (
    calculate_precision,
    calculate_recall,
    calculate_hit_rate,
    calculate_mrr,
    calculate_ndcg,
    evaluate_retrieval_dataset,
)
from app.evaluation.generation_metrics import (
    calculate_faithfulness,
    calculate_answer_relevancy,
    calculate_answer_correctness,
    calculate_chain_of_thought_quality,
    evaluate_generation,
)
from app.evaluation.evaluator import RAGEvaluator


class TestRetrievalMetrics(unittest.TestCase):

    def test_precision(self):
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3"}
        
        # Top 3 -> ["doc1", "doc2", "doc3"] -> 2 relevant -> Precision@3 = 2/3 = 0.6667
        p3 = calculate_precision(retrieved, relevant, k=3)
        self.assertAlmostEqual(p3, 2 / 3, places=3)

        # Top 5 -> 2 relevant -> Precision@5 = 2/5 = 0.4
        p5 = calculate_precision(retrieved, relevant, k=5)
        self.assertEqual(p5, 0.4)

        # Edge cases
        self.assertEqual(calculate_precision([], relevant, k=5), 0.0)
        self.assertEqual(calculate_precision(retrieved, set(), k=5), 0.0)

    def test_recall(self):
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc3", "doc4", "doc5"}  # 4 total relevant

        # Top 3 -> 2 relevant retrieved out of 4 -> Recall@3 = 2/4 = 0.5
        r3 = calculate_recall(retrieved, relevant, k=3)
        self.assertEqual(r3, 0.5)

        self.assertEqual(calculate_recall(retrieved, set(), k=3), 0.0)

    def test_hit_rate(self):
        retrieved = ["doc1", "doc2", "doc3"]
        
        # Hit at rank 1
        self.assertEqual(calculate_hit_rate(retrieved, {"doc1"}, k=3), 1.0)

        # Hit at rank 3
        self.assertEqual(calculate_hit_rate(retrieved, {"doc3"}, k=3), 1.0)

        # Miss
        self.assertEqual(calculate_hit_rate(retrieved, {"doc99"}, k=3), 0.0)

    def test_mrr(self):
        retrieved = ["doc10", "doc20", "doc30", "doc40"]

        # First relevant doc is rank 1 -> RR = 1/1 = 1.0
        self.assertEqual(calculate_mrr(retrieved, {"doc10"}, k=4), 1.0)

        # First relevant doc is rank 2 -> RR = 1/2 = 0.5
        self.assertEqual(calculate_mrr(retrieved, {"doc20"}, k=4), 0.5)

        # First relevant doc is rank 3 -> RR = 1/3
        self.assertAlmostEqual(calculate_mrr(retrieved, {"doc30"}, k=4), 1 / 3, places=3)

        # No relevant doc in top 4 -> RR = 0.0
        self.assertEqual(calculate_mrr(retrieved, {"doc99"}, k=4), 0.0)

    def test_ndcg(self):
        retrieved = ["doc1", "doc2", "doc3"]

        # Ideal ranking order
        graded_rel = {"doc1": 3.0, "doc2": 2.0, "doc3": 1.0}
        ndcg_ideal = calculate_ndcg(retrieved, graded_rel, k=3)
        self.assertEqual(ndcg_ideal, 1.0)

        # Non-ideal order
        reversed_retrieved = ["doc3", "doc2", "doc1"]
        ndcg_reversed = calculate_ndcg(reversed_retrieved, graded_rel, k=3)
        self.assertGreater(ndcg_ideal, ndcg_reversed)
        self.assertGreater(ndcg_reversed, 0.0)


class TestGenerationMetrics(unittest.TestCase):

    def test_faithfulness(self):
        context = ["Drag is a RAG framework powered by FastAPI and React."]
        answer = "Drag is a high performance RAG framework using FastAPI and React."
        res = calculate_faithfulness(answer, context)
        self.assertGreater(res["score"], 0.7)

    def test_answer_relevancy(self):
        query = "What database does Drag use for vector search?"
        answer = "Drag uses FAISS as its vector search database."
        res = calculate_answer_relevancy(query, answer)
        self.assertGreater(res["score"], 0.5)

    def test_answer_correctness(self):
        generated = "FAISS is used for semantic vector retrieval in Drag."
        reference = "Drag utilizes FAISS vector index for semantic search retrieval."
        res = calculate_answer_correctness(generated, reference)
        self.assertGreater(res["score"], 0.5)

    def test_chain_of_thought_quality(self):
        contexts = ["Drag architecture integrates BM25 for sparse keyword matching and FAISS for dense vectors."]
        trace = "First, examine query keywords. Second, compare BM25 and FAISS embeddings. Therefore, hybrid search combines both."
        answer = "Hybrid search combines BM25 and FAISS."

        res = calculate_chain_of_thought_quality(trace, contexts, answer)
        self.assertTrue(res["has_cot_structure"])
        self.assertGreater(res["score"], 0.5)


class TestRAGEvaluator(unittest.TestCase):

    def test_evaluator_dataset(self):
        evaluator = RAGEvaluator(default_k=3)
        dataset = [
            {
                "query": "What is Drag?",
                "retrieved_ids": ["chunk1", "chunk2", "chunk3"],
                "relevant_ids": ["chunk1"],
                "generated_answer": "Drag is an enterprise RAG accelerator platform.",
                "retrieved_contexts": ["Drag is an enterprise RAG accelerator platform for document search."],
            }
        ]

        results = evaluator.evaluate_dataset(dataset, k=3)
        self.assertIn("summary", results)
        summary = results["summary"]
        self.assertEqual(summary["retrieval"]["hit_rate"], 1.0)
        self.assertEqual(summary["retrieval"]["mrr"], 1.0)
        self.assertGreater(summary["generation"]["mean_faithfulness"], 0.5)


if __name__ == "__main__":
    unittest.main()
