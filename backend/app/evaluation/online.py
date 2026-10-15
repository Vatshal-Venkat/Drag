# backend/app/evaluation/online.py
"""
Online (production) RAG evaluation.

After each strict-RAG answer, the conversation engine hands the query, the
contexts it used and the final answer to `submit_online_evaluation`. Scoring
runs on a single background worker so chat streaming is never delayed, and
each result is appended as one JSON line to the evaluation log.

Live traffic has no ground truth, so only reference-free metrics are computed:
context relevance, faithfulness and answer relevancy.

Environment:
  RAG_ONLINE_EVAL              off | heuristic | llm      (default: heuristic)
  RAG_ONLINE_EVAL_SAMPLE_RATE  0.0-1.0 share of answers scored in llm mode (default: 1.0)
  RAG_EVAL_LOG_PATH            JSONL file (default: backend/eval_logs/online_evals.jsonl)
  RAG_EVAL_FAITHFULNESS_THRESHOLD  answers below this are flagged (default: 0.85)
"""

import json
import os
import random
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.evaluation.generation_metrics import evaluate_generation
from app.evaluation.llm_judge import LLMJudge

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ONLINE_EVAL_MODE = os.getenv("RAG_ONLINE_EVAL", "heuristic").lower()
ONLINE_EVAL_SAMPLE_RATE = float(os.getenv("RAG_ONLINE_EVAL_SAMPLE_RATE", 1.0))
EVAL_LOG_PATH = os.getenv(
    "RAG_EVAL_LOG_PATH",
    os.path.join(_BACKEND_DIR, "eval_logs", "online_evals.jsonl"),
)
FAITHFULNESS_THRESHOLD = float(os.getenv("RAG_EVAL_FAITHFULNESS_THRESHOLD", 0.85))

MAX_LOGGED_TEXT_CHARS = 2000

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rag-online-eval")
_write_lock = threading.Lock()
_judge: Optional[LLMJudge] = None


def _get_judge() -> LLMJudge:
    global _judge
    if _judge is None:
        _judge = LLMJudge()
    return _judge


def build_record(
    *,
    session_id: str,
    query: str,
    rewritten_query: Optional[str],
    answer: str,
    contexts: List[Dict[str, Any]],
    use_llm_judge: bool,
) -> Dict[str, Any]:
    """Score one answer and build the log record (runs on the worker thread)."""
    context_texts = [c.get("text", "") for c in contexts]
    metrics = evaluate_generation(
        user_query=query,
        generated_answer=answer,
        retrieved_contexts=context_texts,
        llm_evaluator=_get_judge() if use_llm_judge else None,
    )

    faithfulness = metrics["faithfulness"]["score"]
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "query": query[:MAX_LOGGED_TEXT_CHARS],
        "rewritten_query": (rewritten_query or "")[:MAX_LOGGED_TEXT_CHARS],
        "answer": answer[:MAX_LOGGED_TEXT_CHARS],
        "retrieved": [
            {
                "id": c.get("id"),
                "source": c.get("source"),
                "page": c.get("page"),
                "document_id": c.get("document_id"),
                "final_score": c.get("final_score"),
                "semantic_score": c.get("_semantic_score"),
            }
            for c in contexts
        ],
        "mode": "llm" if use_llm_judge else "heuristic",
        "metrics": metrics,
        "flagged": faithfulness < FAITHFULNESS_THRESHOLD,
    }


def _append_record(record: Dict[str, Any], log_path: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, default=str)
    with _write_lock:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def _run(kwargs: Dict[str, Any], log_path: str) -> None:
    try:
        _append_record(build_record(**kwargs), log_path)
    except Exception as e:
        print(f"[OnlineEval] evaluation failed: {e}")


def submit_online_evaluation(
    *,
    session_id: str,
    query: str,
    answer: str,
    contexts: List[Dict[str, Any]],
    rewritten_query: Optional[str] = None,
) -> bool:
    """
    Queue an answer for background scoring. Never raises.
    Returns True if the answer was queued.
    """
    try:
        if ONLINE_EVAL_MODE == "off" or not answer or not contexts:
            return False

        use_llm = ONLINE_EVAL_MODE == "llm" and random.random() < ONLINE_EVAL_SAMPLE_RATE

        _executor.submit(
            _run,
            {
                "session_id": session_id,
                "query": query,
                "rewritten_query": rewritten_query,
                "answer": answer,
                # Copy: the engine may keep mutating its chunk dicts
                "contexts": [dict(c) for c in contexts],
                "use_llm_judge": use_llm,
            },
            EVAL_LOG_PATH,
        )
        return True
    except Exception as e:
        print(f"[OnlineEval] could not queue evaluation: {e}")
        return False


# ==========================================================
# READ / AGGREGATE
# ==========================================================

def read_records(limit: int = 100, log_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Most recent records first."""
    path = log_path or EVAL_LOG_PATH
    if not os.path.exists(path):
        return []

    with _write_lock:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    records = []
    for line in reversed(lines):
        if len(records) >= limit:
            break
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate online evaluation records into dashboard-friendly stats."""
    if not records:
        return {"total_evaluated": 0}

    def mean_of(path: List[str]) -> Optional[float]:
        values = []
        for r in records:
            node: Any = r.get("metrics", {})
            for key in path:
                node = node.get(key) if isinstance(node, dict) else None
            if isinstance(node, (int, float)):
                values.append(float(node))
        return round(sum(values) / len(values), 4) if values else None

    flagged = [r for r in records if r.get("flagged")]
    return {
        "total_evaluated": len(records),
        "llm_judged": sum(1 for r in records if r.get("mode") == "llm"),
        "mean_rag_triad_score": mean_of(["rag_triad_score"]),
        "mean_context_relevance": mean_of(["context_relevance", "score"]),
        "mean_context_precision": mean_of(["context_relevance", "context_precision"]),
        "mean_faithfulness": mean_of(["faithfulness", "score"]),
        "mean_answer_relevancy": mean_of(["answer_relevancy", "score"]),
        "faithfulness_threshold": FAITHFULNESS_THRESHOLD,
        "flagged_count": len(flagged),
        "flagged_rate": round(len(flagged) / len(records), 4),
        "recent_flagged": [
            {
                "id": r.get("id"),
                "timestamp": r.get("timestamp"),
                "query": r.get("query"),
                "faithfulness": r.get("metrics", {}).get("faithfulness", {}).get("score"),
            }
            for r in flagged[:10]
        ],
        "window": {
            "oldest": records[-1].get("timestamp"),
            "newest": records[0].get("timestamp"),
        },
    }
