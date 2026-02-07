from typing import List
import os
from google import genai
from google.genai import types  # Import types for configuration

# ==================================================
# EMBEDDING CONFIG
# ==================================================

# Match your existing Vector Store (768)
EMBED_DIM = 768
BATCH_SIZE = 100 
_client = None

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client

# ==================================================
# PUBLIC EMBEDDING API
# ==================================================

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Converts text chunks into 768-dim vectors using gemini-embedding-001.
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        
        # We pass output_dimensionality to fix the 3072 mismatch
        response = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=batch,
            config=types.EmbedContentConfig(
                task_type='RETRIEVAL_DOCUMENT',
                output_dimensionality=EMBED_DIM,  # Forces 768
                title='Document Chunks'
            )
        )

        if response.embeddings:
            batch_vectors = [e.values for e in response.embeddings]
            all_embeddings.extend(batch_vectors)

    return all_embeddings


def embed_query(query: str) -> List[float]:
    """
    Converts a search query into a 768-dim vector.
    """
    if not query:
        return []

    client = _get_client()

    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=[query],
        config=types.EmbedContentConfig(
            task_type='RETRIEVAL_QUERY',
            output_dimensionality=EMBED_DIM  # Forces 768
        )
    )

    if not response.embeddings:
        raise RuntimeError("No embeddings returned")

    return response.embeddings[0].values