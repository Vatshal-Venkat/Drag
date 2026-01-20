from typing import List, Dict
from app.services.embeddings import embed_texts
from app.vectorstore.store_manager import get_store_for_document


def retrieve_context(
    query: str,
    top_k: int,
    document_id: str,
) -> List[Dict]:
    """
    Retrieve top-k chunks from a single document's FAISS index.
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
