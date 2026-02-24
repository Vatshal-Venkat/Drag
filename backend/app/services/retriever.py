# backend/app/services/retriever.py

from typing import List, Dict, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

from app.services.embeddings import embed_query, embed_texts
from app.vectorstore.store_manager import (
    get_store_for_document,
    list_all_document_stores,
    get_bm25_for_store,
)
TOP_DOCS = 3
MAX_CHUNKS_PER_DOC = 2

SEMANTIC_WEIGHT_FACTUAL = 0.8
BM25_WEIGHT_FACTUAL = 0.2

SEMANTIC_WEIGHT_CONCEPTUAL = 0.4
BM25_WEIGHT_CONCEPTUAL = 0.6

RERANK_CONFIDENCE_THRESHOLD = 0.75


# ==================================================
# 🔹 COSINE SIMILARITY
# ==================================================

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ==================================================
# 🔹 HYBRID SECTION ALIGNMENT
# ==================================================

def align_sections_hybrid(
    grouped_contexts: Dict[str, List[Dict]]
) -> List[Dict]:
    """
    Hybrid alignment:
    1. Compute embeddings per chunk
    2. Pair chunks via cosine similarity
    3. LLM will later refine structured diff
    """

    doc_ids = list(grouped_contexts.keys())
    if len(doc_ids) < 2:
        return []

    # Currently aligning first two documents only
    doc_a, doc_b = doc_ids[0], doc_ids[1]

    contexts_a = grouped_contexts.get(doc_a, [])
    contexts_b = grouped_contexts.get(doc_b, [])

    if not contexts_a or not contexts_b:
        return []

    texts_a = [c.get("text", "") for c in contexts_a]
    texts_b = [c.get("text", "") for c in contexts_b]

    embeddings_a = embed_texts(texts_a)
    embeddings_b = embed_texts(texts_b)

    aligned_sections = []

    for idx_a, emb_a in enumerate(embeddings_a):
        best_idx = None
        best_score = -1.0

        for idx_b, emb_b in enumerate(embeddings_b):
            score = _cosine_similarity(emb_a, emb_b)

            if score > best_score:
                best_score = score
                best_idx = idx_b

        if best_idx is not None:
            aligned_sections.append({
                "section_id": len(aligned_sections) + 1,
                doc_a: contexts_a[idx_a],
                doc_b: contexts_b[best_idx],
                "similarity": round(best_score, 4),
            })

    return aligned_sections


# ==================================================
# EXISTING LOGIC BELOW (UNCHANGED)
# ==================================================

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



def _should_rerank(contexts: List[Dict]) -> bool:
    if not contexts:
        return False
    avg_conf = sum(
        float(c.get("final_score", c.get("confidence", 0.0)))
        for c in contexts
    ) / len(contexts)
    return avg_conf < RERANK_CONFIDENCE_THRESHOLD


# --------------------------------------------------
# DOCUMENT-SCOPED RETRIEVAL (STRICT)
# --------------------------------------------------

def retrieve_context(
    query: str,
    top_k: int,
    document_id: str,
) -> List[Dict]:

    store = get_store_for_document(document_id)
    query_embedding = embed_query(query)

    results = store.search(query_embedding, k=top_k)

    contexts: List[Dict] = []

    for r in results:
        context = {
            "id": r.get("id"),
            "text": r.get("text", ""),
            "source": r.get("source", "unknown"),
            "page": r.get("page"),
            "confidence": r.get("confidence", 0.0),
            "document_id": document_id,
            "agent": "retrieval_agent",
        }

        if context["text"]:
            contexts.append(context)

    return contexts


# --------------------------------------------------
# COMPARISON RETRIEVAL (PARALLEL + SAFE)
# --------------------------------------------------

def retrieve_for_comparison(
    *,
    query: str,
    document_ids: List[str],
    top_k: int,
) -> Dict[str, List[Dict]]:

    grouped_contexts: Dict[str, List[Dict]] = {}

    with ThreadPoolExecutor(
        max_workers=min(len(document_ids), 4)
    ) as executor:

        futures = {
            executor.submit(
                retrieve_context,
                query,
                top_k,
                doc_id,
            ): doc_id
            for doc_id in document_ids
        }

        for future in as_completed(futures):
            doc_id = futures[future]
            try:
                grouped_contexts[doc_id] = future.result()
            except Exception:
                grouped_contexts[doc_id] = []

    return grouped_contexts


# --------------------------------------------------
# AGENTIC RETRIEVAL ENTRYPOINT
# --------------------------------------------------

def retrieve(
    query: str,
    k: int = 5,
    document_id: Optional[str] = None,
) -> List[Dict]:

    if document_id:
        return retrieve_context(query, k, document_id)

    stores = list_all_document_stores()
    if not stores:
        return []

    query_embedding = embed_query(query)
    query_tokens = query.lower().split()

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
        if not semantic_hits:
            continue

        bm25 = get_bm25_for_store(store)
        bm25_scores = bm25.get_scores(query_tokens)
        max_bm25 = float(bm25_scores.max()) if len(bm25_scores) > 0 else 1.0

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

            if "skill" in query.lower():
                if "skill" in hit.get("text", "").lower():
                    final_score += 0.2

            enriched = dict(hit)
            enriched["final_score"] = round(final_score, 4)
            enriched["_doc_id"] = store_id
            enriched["agent"] = "retrieval_agent"

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

    suggest_rerank = _should_rerank(final_chunks)

    for c in final_chunks:
        c["_suggest_rerank"] = suggest_rerank

    return final_chunks[:k]
