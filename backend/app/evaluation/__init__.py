# backend/app/evaluation/__init__.py
"""
RAG Evaluation Module for Drag Accelerator.
Includes retrieval metrics (Precision, Recall, Hit Rate, MRR, NDCG)
and generation/reasoning metrics (Context Relevance, Faithfulness, Answer Relevancy,
Answer Correctness, Chain of Thought), scored by an optional LLM judge with heuristic fallback.
"""

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

from app.evaluation.llm_judge import LLMJudge

__all__ = [
    "LLMJudge",
    "calculate_context_relevance",
    "calculate_precision",
    "calculate_recall",
    "calculate_hit_rate",
    "calculate_mrr",
    "calculate_ndcg",
    "evaluate_retrieval_dataset",
    "calculate_faithfulness",
    "calculate_answer_relevancy",
    "calculate_answer_correctness",
    "calculate_chain_of_thought_quality",
    "evaluate_generation",
]
