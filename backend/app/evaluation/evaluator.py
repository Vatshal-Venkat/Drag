# backend/app/evaluation/evaluator.py
"""
Unified RAG Evaluator for Drag Accelerator.
Runs end-to-end evaluations combining Retrieval Metrics
(Precision, Recall, Hit Rate, MRR, NDCG) and Generation/Reasoning Metrics
(Context Relevance, Faithfulness, Relevancy, Correctness, Chain of Thought).
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


def _mean(values: List[float]) -> Optional[float]:
    return round(sum(values) / len(values), 4) if values else None


class RAGEvaluator:
    """Unified benchmark evaluator for Drag RAG system."""

    def __init__(self, default_k: int = 5, llm_evaluator: Optional[Any] = None):
        self.default_k = default_k
        # Optional LLM judge (app.evaluation.llm_judge.LLMJudge); heuristics are used when None
        self.llm_evaluator = llm_evaluator

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
            llm_evaluator=self.llm_evaluator,
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
        collected: Dict[str, List[float]] = {
            "rag_triad_score": [],
            "overall_score": [],
            "context_relevance": [],
            "context_precision": [],
            "faithfulness": [],
            "answer_relevancy": [],
            "answer_correctness": [],
            "chain_of_thought_quality": [],
        }
        llm_judged_metrics = 0
        total_metrics = 0

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
            collected["rag_triad_score"].append(gen["rag_triad_score"])
            collected["overall_score"].append(gen["overall_score"])
            collected["context_precision"].append(gen["context_relevance"]["context_precision"])
            for key in ("context_relevance", "faithfulness", "answer_relevancy",
                        "answer_correctness", "chain_of_thought_quality"):
                metric = gen.get(key)
                if metric:
                    collected[key].append(metric["score"])
                    total_metrics += 1
                    if metric.get("method") == "llm":
                        llm_judged_metrics += 1

        retrieval_summary = evaluate_retrieval_dataset(retrieval_samples, k=k_val)

        generation_summary = {f"mean_{key}": _mean(values) for key, values in collected.items()}
        generation_summary["llm_judged_ratio"] = (
            round(llm_judged_metrics / total_metrics, 4) if total_metrics else 0.0
        )

        return {
            "summary": {
                "retrieval": retrieval_summary,
                "generation": generation_summary,
                "total_samples": len(dataset),
            },
            "detailed_samples": sample_evals,
        }
