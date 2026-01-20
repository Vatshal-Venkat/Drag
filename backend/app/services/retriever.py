from typing import List, Dict
from app.services.embeddings import embed_texts
from app.vectorstore.faiss_store import FAISSStore

# Single global vector store
store = FAISSStore(dim=384)


def retrieve_context(query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve top-k chunks safely.
    Never crashes on missing fields.
    """

    # Embed query
    query_embedding = embed_texts([query])[0]

    # Vector search
    results = store.search(query_embedding, k=top_k)

    contexts: List[Dict] = []

    for idx, r in enumerate(results):
        # Defensive extraction — FAISS results are NOT guaranteed uniform
        context = {
            "id": (
                r.get("id")
                or r.get("metadata", {}).get("id")
                or f"chunk-{idx}"
            ),
            "text": (
                r.get("text")
                or r.get("page_content")
                or ""
            ),
            "source": (
                r.get("source")
                or r.get("metadata", {}).get("source")
                or "unknown"
            ),
            "page": (
                r.get("page")
                or r.get("metadata", {}).get("page")
            ),
            "confidence": (
                r.get("confidence")
                or r.get("score")
                or 0.0
            ),
        }

        # Skip empty chunks (important)
        if not context["text"]:
            continue

        contexts.append(context)

    return contexts
