from typing import List
from sentence_transformers import SentenceTransformer

# Load once (global)
_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings locally using SentenceTransformers.
    Free, fast, FAISS-compatible.
    """
    if not texts:
        return []

    embeddings = _model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embeddings.tolist()
