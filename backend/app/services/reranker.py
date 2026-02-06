from typing import List, Dict


def rerank_contexts(
    query: str,
    contexts: List[Dict],
    top_k: int = 4,
) -> List[Dict]:
    """
    Reranker disabled.
    SentenceTransformers removed to keep memory usage low.

    Contexts are returned in their original order
    (already ranked by vector + BM25 retrieval).
    """

    if not contexts:
        return []

    # Mark provenance for debugging / transparency
    for c in contexts:
        c["agent"] = "retriever_agent"

    return contexts[:top_k]
