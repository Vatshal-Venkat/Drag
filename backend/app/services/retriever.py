from typing import List, Dict, Optional
from collections import defaultdict

from rank_bm25 import BM25Okapi

from app.services.embeddings import embed_texts
from app.vectorstore.store_manager import (
    get_store_for_document,
    list_all_document_stores,
)

TOP_DOCS = 3
MAX_CHUNKS_PER_DOC = 2

SEMANTIC_WEIGHT_FACTUAL = 0.8
BM25_WEIGHT_FACTUAL = 0.2

SEMANTIC_WEIGHT_CONCEPTUAL = 0.4
BM25_WEIGHT_CONCEPTUAL = 0.6


def _is_conceptual_query(query: str) -> bool:
    keywords = [
        "explain",
        "what is",
        "overview",
        "theory",
        "concept",
        "how does",
        "describe",
        "introduction",
    ]
    q = query.lower()
    return any(k in q for k in keywords)


def retrieve_context(
    query: str,
    top_k: int,
    document_id: str,
) -> List[Dict]:
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


def retrieve(
    query: str,
    k: int = 5,
    document_id: Optional[str] = None,
) -> List[Dict]:
    """
    Document-isolated by default.
    Multi-document only when document_id is None.
    """

    query_embedding = embed_texts([query])[0]
    query_tokens = query.lower().split()

    # --------------------------------------------------
    # STRICT DOCUMENT ISOLATION
    # --------------------------------------------------
    if document_id:
        return retrieve_context(query, k, document_id)

    # --------------------------------------------------
    # MULTI-DOCUMENT MODE (explicit only)
    # --------------------------------------------------
    stores = list_all_document_stores()
    if not stores:
        return []

    if _is_conceptual_query(query):
        semantic_weight = SEMANTIC_WEIGHT_CONCEPTUAL
        bm25_weight = BM25_WEIGHT_CONCEPTUAL
    else:
        semantic_weight = SEMANTIC_WEIGHT_FACTUAL
        bm25_weight = BM25_WEIGHT_FACTUAL

    doc_chunks: Dict[str, List[Dict]] = defaultdict(list)
    doc_scores: Dict[str, float] = {}

    for store in stores:
        semantic_hits = store.search(query_embedding, k=k)

        corpus = store.get_all_texts()
        if not corpus:
            continue

        if not hasattr(store, "_bm25_cache"):
            tokenized = [doc.lower().split() for doc in corpus]
            store._bm25_cache = {
                "size": len(corpus),
                "bm25": BM25Okapi(tokenized),
            }

        if store._bm25_cache["size"] != len(corpus):
            tokenized = [doc.lower().split() for doc in corpus]
            store._bm25_cache = {
                "size": len(corpus),
                "bm25": BM25Okapi(tokenized),
            }

        bm25 = store._bm25_cache["bm25"]
        bm25_scores = bm25.get_scores(query_tokens)
        max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 else 1.0

        store_id = store.store_dir

        for hit in semantic_hits:
            idx = hit["id"]
            bm25_score = (
                bm25_scores[idx] / max_bm25
                if idx < len(bm25_scores)
                else 0.0
            )

            final_score = (
                semantic_weight * hit.get("confidence", 0.0)
                + bm25_weight * bm25_score
            )

            enriched = dict(hit)
            enriched["final_score"] = round(final_score, 4)
            enriched["_doc_id"] = store_id

            doc_chunks[store_id].append(enriched)

        if doc_chunks[store_id]:
            top_scores = sorted(
                (c["final_score"] for c in doc_chunks[store_id]),
                reverse=True
            )[:MAX_CHUNKS_PER_DOC]

            doc_scores[store_id] = sum(top_scores) / len(top_scores)

    top_doc_ids = sorted(
        doc_scores.keys(),
        key=lambda d: doc_scores[d],
        reverse=True
    )[:TOP_DOCS]

    final_chunks: List[Dict] = []
    for doc_id in top_doc_ids:
        final_chunks.extend(
            sorted(
                doc_chunks[doc_id],
                key=lambda c: c["final_score"],
                reverse=True
            )[:MAX_CHUNKS_PER_DOC]
        )

    final_chunks.sort(key=lambda c: c["final_score"], reverse=True)

    for c in final_chunks:
        c.pop("_doc_id", None)

    return final_chunks[:k]
