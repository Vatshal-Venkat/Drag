# backend/app/api/evaluation.py
"""
FastAPI Endpoints for RAG Evaluation (Retrieval + Generation Metrics).
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.evaluation.retrieval_metrics import (
    calculate_precision,
    calculate_recall,
    calculate_hit_rate,
    calculate_mrr,
    calculate_ndcg,
    evaluate_retrieval_dataset,
)
from app.evaluation.generation_metrics import evaluate_generation
from app.evaluation.evaluator import RAGEvaluator

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


class RetrievalEvalRequest(BaseModel):
    retrieved_ids: List[str] = Field(..., description="IDs of retrieved document chunks in order")
    relevant_ids: List[str] = Field(..., description="Ground-truth relevant document IDs")
    relevance_scores: Optional[Dict[str, float]] = Field(None, description="Graded relevance scores for NDCG")
    k: int = Field(5, description="Top-K cutoff parameter")


class GenerationEvalRequest(BaseModel):
    user_query: str
    generated_answer: str
    retrieved_contexts: List[str]
    reference_answer: Optional[str] = None
    reasoning_trace: Optional[str] = None


class BatchEvaluationRequest(BaseModel):
    k: int = 5
    samples: List[Dict[str, Any]]


@router.post("/retrieval")
def evaluate_retrieval(req: RetrievalEvalRequest):
    """Compute retrieval metrics (Precision, Recall, Hit Rate, MRR, NDCG) for a single query."""
    rel_map = req.relevance_scores if req.relevance_scores else req.relevant_ids
    return {
        "precision": calculate_precision(req.retrieved_ids, req.relevant_ids, k=req.k),
        "recall": calculate_recall(req.retrieved_ids, req.relevant_ids, k=req.k),
        "hit_rate": calculate_hit_rate(req.retrieved_ids, req.relevant_ids, k=req.k),
        "mrr": calculate_mrr(req.retrieved_ids, req.relevant_ids, k=req.k),
        "ndcg": calculate_ndcg(req.retrieved_ids, rel_map, k=req.k),
        "k": req.k,
    }


@router.post("/generation")
def evaluate_generation_endpoint(req: GenerationEvalRequest):
    """Compute generation metrics (Faithfulness, Relevancy, Correctness, Chain of Thought Quality)."""
    return evaluate_generation(
        user_query=req.user_query,
        generated_answer=req.generated_answer,
        retrieved_contexts=req.retrieved_contexts,
        reference_answer=req.reference_answer,
        reasoning_trace=req.reasoning_trace,
    )


@router.post("/batch")
def evaluate_batch_endpoint(req: BatchEvaluationRequest):
    """Run full dataset batch evaluation across both retrieval and generation metrics."""
    evaluator = RAGEvaluator(default_k=req.k)
    return evaluator.evaluate_dataset(req.samples, k=req.k)
