from typing import List, Dict, Optional

from rank_bm25 import BM25Okapi

from app.services.embeddings import embed_texts
from app.vectorstore.store_manager import (
    get_store_for_document,
    get_default_store,
    list_all_document_stores,
)


def retrieve_context(
    query: str,
    top_k: int,
    document_id: str,
) -> List[Dict]:
    """
    Retrieve top-k chunks from a single document's FAISS index.
    (Existing behavior — DO NOT BREAK)
    """

    store = get_store_for_document(document_id)

    query_embedding = embed_texts([query])[0]
    results = store.search(query_embedding, k=top_k)

    contexts: List[Dict] = []

    for r in results:
        context = {
            "id": r.get("id"),
            "text": r.get("text", ""),
            "source": r.get("source", "unknown"),
            "page": r.get("page"),
            "confidence": r.get("confidence", 0.0),
        }

        if context["text"]:
            contexts.append(context)

    return contexts


# -------------------------
# Chat-compatible retriever
# -------------------------

def retrieve(
    query: str,
    k: int = 5,
    document_id: Optional[str] = None,
) -> List[Dict]:
    """
    Generic retriever for ChatGPT-style chat.

    Behavior:
    - If document_id is provided → scoped retrieval (UNCHANGED)
    - Else → multi-document hybrid retrieval (NEW)
    """

    # ------------------------------------
    # EXISTING SINGLE-DOCUMENT BEHAVIOR
    # ------------------------------------
    if document_id:
        store = get_store_for_document(document_id)

        query_embedding = embed_texts([query])[0]
        results = store.search(query_embedding, k=k)

        contexts: List[Dict] = []

        for r in results:
            context = {
                "id": r.get("id"),
                "text": r.get("text", ""),
                "source": r.get("source", "unknown"),
                "page": r.get("page"),
                "confidence": r.get("confidence", 0.0),
            }

            if context["text"]:
                contexts.append(context)

        return contexts

    # ------------------------------------
    # 🔹 NEW: MULTI-DOCUMENT HYBRID MODE
    # ------------------------------------

    stores = list_all_document_stores()
    if not stores:
        return []

    query_embedding = embed_texts([query])[0]
    query_tokens = query.lower().split()

    all_results: List[Dict] = []

    for store in stores:
        # Semantic search (FAISS)
        semantic_hits = store.search(query_embedding, k=k)

        # BM25 lexical search
        corpus = store.get_all_texts()
        if not corpus:
            continue

        tokenized_corpus = [doc.lower().split() for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(query_tokens)

        max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 else 1.0

        for hit in semantic_hits:
            idx = hit["id"]

            bm25_score = (
                bm25_scores[idx] / max_bm25
                if idx < len(bm25_scores)
                else 0.0
            )

            final_score = (
                0.7 * hit.get("confidence", 0.0)
                + 0.3 * bm25_score
            )

            enriched = dict(hit)
            enriched["bm25_score"] = round(float(bm25_score), 4)
            enriched["final_score"] = round(float(final_score), 4)

            all_results.append(enriched)

    # Global re-ranking
    all_results.sort(key=lambda x: x["final_score"], reverse=True)

    return all_results[:k]
