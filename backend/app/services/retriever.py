from app.core.embeddings import embed_texts
from app.vectorstore.faiss_store import FAISSStore

store = FAISSStore(dim=384)

def retrieve(query: str, top_k=5):
    query_embedding = embed_texts([query])
    results = store.search(query_embedding, k=top_k)
    return results
