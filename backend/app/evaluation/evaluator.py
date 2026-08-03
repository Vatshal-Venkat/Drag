# backend/app/evaluation/evaluator.py
"""
Unified RAG Evaluator for Drag Accelerator.
Runs end-to-end evaluations combining Retrieval Metrics
(Precision, Recall, Hit Rate, MRR, NDCG) and Generation/Reasoning Metrics
(Faithfulness, Relevancy, Correctness, Chain of Thought).
"""

from typing import List, Dict, Any, Optional
from app.evaluation.retrieval_metrics import (
    calculate_precision,
    calculate_recall,
    calculate_hit_rate,
    calculate_mrr,
    calculate_ndcg,
    evaluate_retrieval_dataset,
)
from app.evaluation.generation_metrics import evaluate_generation


class RAGEvaluator:
    """Unified benchmark evaluator for Drag RAG system."""

    def __init__(self, default_k: int = 5):
        self.default_k = default_k

    def evaluate_sample(
        self,
        query: str,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        generated_answer: str,
        retrieved_contexts: List[str],
        reference_answer: Optional[str] = None,
        reasoning_trace: Optional[str] = None,
        relevance_scores: Optional[Dict[str, float]] = None,
        k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Evaluates a single query sample for both retrieval and generation performance."""
        k_val = k if k is not None else self.default_k
        scores_map = relevance_scores if relevance_scores else relevant_ids

        retrieval_results = {
            "precision": calculate_precision(retrieved_ids, relevant_ids, k=k_val),
            "recall": calculate_recall(retrieved_ids, relevant_ids, k=k_val),
            "hit_rate": calculate_hit_rate(retrieved_ids, relevant_ids, k=k_val),
            "mrr": calculate_mrr(retrieved_ids, relevant_ids, k=k_val),
            "ndcg": calculate_ndcg(retrieved_ids, scores_map, k=k_val),
            "k": k_val,
        }

        generation_results = evaluate_generation(
            user_query=query,
            generated_answer=generated_answer,
            retrieved_contexts=retrieved_contexts,
            reference_answer=reference_answer,
            reasoning_trace=reasoning_trace,
        )

        return {
            "query": query,
            "retrieval": retrieval_results,
            "generation": generation_results,
        }

    def evaluate_dataset(
        self,
        dataset: List[Dict[str, Any]],
        k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates a list of test dataset samples.
        Aggregates mean retrieval and generation scores.
        """
        k_val = k if k is not None else self.default_k
        if not dataset:
            return {"error": "Empty dataset"}

        sample_evals = []
        retrieval_samples = []
        gen_triad_scores = []
        faithfulness_scores = []
        relevancy_scores = []
        correctness_scores = []

        for sample in dataset:
            res = self.evaluate_sample(
                query=sample.get("query", ""),
                retrieved_ids=sample.get("retrieved_ids", []),
                relevant_ids=sample.get("relevant_ids", []),
                generated_answer=sample.get("generated_answer", ""),
                retrieved_contexts=sample.get("retrieved_contexts", []),
                reference_answer=sample.get("reference_answer"),
                reasoning_trace=sample.get("reasoning_trace"),
                relevance_scores=sample.get("relevance_scores"),
                k=k_val,
            )
            sample_evals.append(res)
            retrieval_samples.append({
                "retrieved_ids": sample.get("retrieved_ids", []),
                "relevant_ids": sample.get("relevant_ids", []),
                "relevance_scores": sample.get("relevance_scores"),
            })

            gen = res["generation"]
            gen_triad_scores.append(gen["rag_triad_score"])
            faithfulness_scores.append(gen["faithfulness"]["score"])
            relevancy_scores.append(gen["answer_relevancy"]["score"])
            if gen.get("answer_correctness"):
                correctness_scores.append(gen["answer_correctness"]["score"])

        retrieval_summary = evaluate_retrieval_dataset(retrieval_samples, k=k_val)

        generation_summary = {
            "mean_rag_triad_score": round(sum(gen_triad_scores) / len(gen_triad_scores), 4),
            "mean_faithfulness": round(sum(faithfulness_scores) / len(faithfulness_scores), 4),
            "mean_answer_relevancy": round(sum(relevancy_scores) / len(relevancy_scores), 4),
            "mean_answer_correctness": (
                round(sum(correctness_scores) / len(correctness_scores), 4)
                if correctness_scores
                else None
            ),
        }

        return {
            "summary": {
                "retrieval": retrieval_summary,
                "generation": generation_summary,
                "total_samples": len(dataset),
            },
            "detailed_samples": sample_evals,
        }
