# backend/app/api/evaluation.py
"""
FastAPI Endpoints for RAG Evaluation (Retrieval + Generation Metrics).
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
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
from app.evaluation.llm_judge import LLMJudge
from app.evaluation import online

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
    use_llm_judge: bool = Field(False, description="Score with the Groq LLM judge (falls back to heuristics on failure)")
    judge_model: Optional[str] = Field(None, description="Override the judge model (default: EVAL_JUDGE_MODEL)")


class BatchEvaluationRequest(BaseModel):
    k: int = 5
    samples: List[Dict[str, Any]]
    use_llm_judge: bool = False
    judge_model: Optional[str] = None


def _judge_for(use_llm_judge: bool, judge_model: Optional[str]) -> Optional[LLMJudge]:
    return LLMJudge(model=judge_model) if use_llm_judge else None


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
    """Compute generation metrics (Context Relevance, Faithfulness, Relevancy, Correctness, CoT Quality)."""
    return evaluate_generation(
        user_query=req.user_query,
        generated_answer=req.generated_answer,
        retrieved_contexts=req.retrieved_contexts,
        reference_answer=req.reference_answer,
        reasoning_trace=req.reasoning_trace,
        llm_evaluator=_judge_for(req.use_llm_judge, req.judge_model),
    )


@router.post("/batch")
def evaluate_batch_endpoint(req: BatchEvaluationRequest):
    """Run full dataset batch evaluation across both retrieval and generation metrics."""
    if not req.samples:
        raise HTTPException(status_code=400, detail="samples must not be empty")
    evaluator = RAGEvaluator(
        default_k=req.k,
        llm_evaluator=_judge_for(req.use_llm_judge, req.judge_model),
    )
    return evaluator.evaluate_dataset(req.samples, k=req.k)


@router.get("/online")
def list_online_evaluations(
    limit: int = Query(50, ge=1, le=1000),
    flagged_only: bool = False,
):
    """Recent evaluations of live chat answers, newest first."""
    records = online.read_records(limit=limit if not flagged_only else 1000)
    if flagged_only:
        records = [r for r in records if r.get("flagged")][:limit]
    return {"mode": online.ONLINE_EVAL_MODE, "records": records}


@router.get("/online/summary")
def online_evaluation_summary(limit: int = Query(500, ge=1, le=10000)):
    """Aggregate quality metrics over the most recent live chat answers."""
    summary = online.summarize_records(online.read_records(limit=limit))
    summary["mode"] = online.ONLINE_EVAL_MODE
    return summary
