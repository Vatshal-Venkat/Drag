from typing import List
import os
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini embedding model dimension
EMBED_DIM = 768


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Gemini (hosted).
    Safe for low-memory environments like Render free tier.
    """
    if not texts:
        return []

    response = genai.embed_content(
        model="models/embedding-001",
        content=texts,
        task_type="retrieval_document",
    )

    # When passing a list, Gemini returns a list of embeddings
    return response["embedding"]


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.
    Uses retrieval_query task type for better search quality.
    """
    response = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query",
    )

    return response["embedding"]
