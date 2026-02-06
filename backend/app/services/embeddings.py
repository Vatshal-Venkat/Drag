from typing import List


model = None

def get_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model



def embed_texts(texts):
    if not texts:
        return []

    model = get_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.tolist()

def embed_query(query: str) -> list:
    """
    Embed a single query string.
    Thin wrapper over embed_texts for retriever usage.
    """
    return embed_texts([query])[0]
