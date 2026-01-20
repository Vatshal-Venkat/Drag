from typing import List, Dict
from sentence_transformers import CrossEncoder

# Load once
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank_contexts(
    query: str,
    contexts: List[Dict],
    top_k: int = 4,
) -> List[Dict]:
    """
    Rerank retrieved chunks using a cross-encoder.
    """

    if not contexts:
        return []

    pairs = [
        (query, c.get("text", ""))
        for c in contexts
    ]

    scores = _reranker.predict(pairs)

    # Attach scores
    for c, score in zip(contexts, scores):
        c["rerank_score"] = float(score)

    # Sort by rerank score
    contexts.sort(
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    return contexts[:top_k]
