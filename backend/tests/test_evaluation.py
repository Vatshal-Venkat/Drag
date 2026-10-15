import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import tempfile
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
    calculate_context_relevance,
    calculate_faithfulness,
    calculate_answer_relevancy,
    calculate_answer_correctness,
    calculate_chain_of_thought_quality,
    evaluate_generation,
)
from app.evaluation.evaluator import RAGEvaluator
from app.evaluation.llm_judge import average_precision
from app.evaluation import online


class StubJudge:
    """Returns canned judge output keyed by a word in the system prompt."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def complete_json(self, system, user):
        self.calls += 1
        for marker, response in self.responses.items():
            if marker in system:
                return response
        return None


class FailingJudge:
    def complete_json(self, system, user):
        raise RuntimeError("Groq unavailable")


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

    def test_dataset_ndcg_without_graded_scores(self):
        # relevance_scores=None must fall back to binary relevance, not zero out NDCG
        dataset = [{"retrieved_ids": ["a", "b"], "relevant_ids": ["a"], "relevance_scores": None}]
        summary = evaluate_retrieval_dataset(dataset, k=2)
        self.assertEqual(summary["mean_ndcg"], 1.0)


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

    def test_context_relevance_heuristic(self):
        query = "Which vector index does Drag use?"
        contexts = [
            "Drag stores embeddings in a FAISS vector index.",
            "The office cafeteria opens at nine.",
        ]
        res = calculate_context_relevance(query, contexts)
        self.assertEqual(res["method"], "heuristic")
        self.assertEqual(res["relevance_flags"], [True, False])
        self.assertEqual(res["score"], 0.5)
        self.assertEqual(res["context_precision"], 1.0)

    def test_average_precision_rewards_early_relevant_chunks(self):
        self.assertEqual(average_precision([True, False, False]), 1.0)
        self.assertAlmostEqual(average_precision([False, False, True]), 1 / 3, places=4)
        self.assertEqual(average_precision([False, False]), 0.0)

    def test_evaluate_generation_reports_triad(self):
        res = evaluate_generation(
            user_query="What is Drag?",
            generated_answer="Drag is an enterprise RAG platform.",
            retrieved_contexts=["Drag is an enterprise RAG platform for documents."],
        )
        triad = (
            res["context_relevance"]["score"]
            + res["faithfulness"]["score"]
            + res["answer_relevancy"]["score"]
        ) / 3
        self.assertAlmostEqual(res["rag_triad_score"], round(triad, 4), places=4)
        self.assertEqual(res["overall_score"], res["rag_triad_score"])


class TestLLMJudgedMetrics(unittest.TestCase):

    def test_llm_faithfulness_catches_paraphrase_and_hallucination(self):
        judge = StubJudge({
            "fact-checking": {
                "claims": [
                    {"claim": "Drag uses FAISS", "verdict": "supported", "reason": ""},
                    {"claim": "Drag was founded in 1999", "verdict": "unsupported", "reason": "not in context"},
                ]
            }
        })
        res = calculate_faithfulness("Drag relies on FAISS. It was founded in 1999.", ["Drag uses FAISS."], judge)
        self.assertEqual(res["method"], "llm")
        self.assertEqual(res["score"], 0.5)
        self.assertEqual(len(res["unsupported_claims"]), 1)

    def test_llm_answer_relevancy_rubric_normalised(self):
        judge = StubJudge({"addresses": {"score": 4, "noncommittal": False, "reason": "minor padding"}})
        res = calculate_answer_relevancy("What is Drag?", "Drag is a RAG platform.", judge)
        self.assertEqual(res["method"], "llm")
        self.assertEqual(res["score"], 0.75)

    def test_llm_answer_correctness_f1(self):
        judge = StubJudge({
            "REFERENCE": {
                "true_positives": ["uses FAISS"],
                "false_positives": [],
                "false_negatives": ["uses BM25"],
                "reason": "",
            }
        })
        res = calculate_answer_correctness("Drag uses FAISS.", "Drag uses FAISS and BM25.", judge)
        self.assertEqual(res["method"], "llm")
        # F1 = 1 / (1 + 0.5 * 1)
        self.assertAlmostEqual(res["score"], 0.6667, places=4)

    def test_llm_context_relevance(self):
        judge = StubJudge({
            "retrieved CONTEXT chunks": {
                "verdicts": [
                    {"index": 0, "relevant": False},
                    {"index": 1, "relevant": True},
                ]
            }
        })
        res = calculate_context_relevance("q about faiss", ["noise", "faiss details"], judge)
        self.assertEqual(res["method"], "llm")
        self.assertEqual(res["relevance_flags"], [False, True])
        self.assertEqual(res["context_precision"], 0.5)

    def test_falls_back_to_heuristic_when_judge_fails(self):
        context = ["Drag is a RAG framework powered by FastAPI and React."]
        answer = "Drag is a RAG framework using FastAPI and React."
        res = calculate_faithfulness(answer, context, FailingJudge())
        self.assertEqual(res["method"], "heuristic")
        self.assertGreater(res["score"], 0.7)

    def test_falls_back_on_malformed_judge_output(self):
        judge = StubJudge({"addresses": {"score": "not a number"}})
        res = calculate_answer_relevancy("What is Drag?", "Drag is a RAG platform.", judge)
        self.assertEqual(res["method"], "heuristic")


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
        self.assertEqual(summary["retrieval"]["mean_ndcg"], 1.0)
        self.assertIsNotNone(summary["generation"]["mean_context_relevance"])
        self.assertIsNone(summary["generation"]["mean_answer_correctness"])
        self.assertEqual(summary["generation"]["llm_judged_ratio"], 0.0)


class TestOnlineEvaluation(unittest.TestCase):

    def test_record_is_logged_and_summarised(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "evals.jsonl")
            contexts = [{"id": "c1", "text": "Drag stores embeddings in a FAISS index.", "source": "a.pdf"}]

            online._run(
                {
                    "session_id": "s1",
                    "query": "Where does Drag store embeddings?",
                    "rewritten_query": None,
                    "answer": "Drag stores embeddings in a FAISS index.",
                    "contexts": contexts,
                    "use_llm_judge": False,
                },
                log_path,
            )

            with open(log_path, encoding="utf-8") as f:
                record = json.loads(f.readline())
            self.assertEqual(record["retrieved"][0]["id"], "c1")
            self.assertEqual(record["mode"], "heuristic")
            self.assertIn("rag_triad_score", record["metrics"])

            records = online.read_records(limit=10, log_path=log_path)
            summary = online.summarize_records(records)
            self.assertEqual(summary["total_evaluated"], 1)
            self.assertIsNotNone(summary["mean_faithfulness"])

    def test_summary_of_empty_log(self):
        self.assertEqual(online.summarize_records([]), {"total_evaluated": 0})


if __name__ == "__main__":
    unittest.main()
