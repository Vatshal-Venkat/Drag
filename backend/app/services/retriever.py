from typing import List, Dict, Optional

from app.services.embeddings import embed_texts
from app.vectorstore.store_manager import (
    get_store_for_document,
    get_default_store,
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
    - If document_id is provided → scoped retrieval
    - Else → uses default/global FAISS store
    """

    # 1️⃣ Choose store
    if document_id:
        store = get_store_for_document(document_id)
    else:
        store = get_default_store()

    if store is None:
        return []

    # 2️⃣ Embed query
    query_embedding = embed_texts([query])[0]

    # 3️⃣ FAISS search
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