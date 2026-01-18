from typing import List, Dict
from app.core.embeddings import embed_texts
from app.vectorstore.faiss_store import FAISSStore

# single global store
store = FAISSStore(dim=384)


def retrieve_context(query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve top-k chunks WITH confidence & page info.
    """
    query_embedding = embed_texts([query])[0]

    results = store.search(query_embedding, k=top_k)

    # enforce minimal shape
    contexts = []
    for r in results:
        contexts.append({
            "id": r["id"],
            "text": r["text"],
            "source": r["source"],
            "page": r.get("page"),
            "confidence": r["confidence"],
        })

    return contexts
