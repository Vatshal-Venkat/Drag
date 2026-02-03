import os
import json
import uuid
from typing import List, Dict
from datetime import datetime

from app.schemas.hitl import HumanFeedback

HITL_STORE_PATH = "backend/hitl_feedback.json"


# -------------------------------------------------
# Internal helpers
# -------------------------------------------------

def _load_feedback() -> List[Dict]:
    if not os.path.exists(HITL_STORE_PATH):
        return []

    with open(HITL_STORE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def _save_feedback(entries: List[Dict]):
    os.makedirs(os.path.dirname(HITL_STORE_PATH), exist_ok=True)
    with open(HITL_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# -------------------------------------------------
# Public API
# -------------------------------------------------

def record_human_feedback(feedback: HumanFeedback) -> HumanFeedback:
    """
    Persist a human correction so it can influence future answers.
    """

    data = _load_feedback()

    record = feedback.dict()
    record["id"] = record.get("id") or str(uuid.uuid4())
    record["created_at"] = datetime.utcnow().isoformat()

    data.append(record)
    _save_feedback(data)

    return HumanFeedback(**record)


def find_relevant_feedback(
    query: str,
    document_ids: List[str],
) -> List[HumanFeedback]:
    """
    Find approved human feedback relevant to this query + documents.
    """

    entries = _load_feedback()
    results: List[HumanFeedback] = []

    for e in entries:
        if not e.get("approved", False):
            continue

        # Simple but effective matching
        if e["query"].lower() != query.lower():
            continue

        if not set(e.get("document_ids", [])).intersection(document_ids):
            continue

        results.append(HumanFeedback(**e))

    return results


# -------------------------------------------------
# 🔹 Injection hook (used by generator)
# -------------------------------------------------

def inject_human_feedback(
    query: str,
    contexts: List[Dict],
) -> List[Dict]:
    """
    Inject human-approved corrections as top-priority context.
    """

    document_ids = list({
        c.get("document_id")
        for c in contexts
        if c.get("document_id")
    })

    feedbacks = find_relevant_feedback(query, document_ids)

    if not feedbacks:
        return contexts

    injected_contexts = []

    for fb in feedbacks:
        injected_contexts.append({
            "id": f"human-{fb.id}",
            "text": fb.corrected_answer,
            "source": "human_feedback",
            "page": None,
            "confidence": 1.0,  # absolute priority
            "document_id": ",".join(fb.document_ids),
        })

    # Human feedback FIRST, then retrieved chunks
    return injected_contexts + contexts
