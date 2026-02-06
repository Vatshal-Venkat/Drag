# =====================================================
# 🔹 MODEL CONFIG
# =====================================================

# Embeddings (hosted – Gemini)
EMBEDDING_PROVIDER = "gemini"
EMBEDDING_MODEL = "models/embedding-001"  # Gemini embeddings

# LLM (Groq-hosted)
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.1-8b-instant"


# =====================================================
# 🔹 CHUNKING CONFIG
# =====================================================

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# =====================================================
# 🔹 RETRIEVAL CONFIG
# =====================================================

TOP_K = 5
