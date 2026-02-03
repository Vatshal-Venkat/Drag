# app/core/config.py

import os

# =====================================================
# 🔹 ENV LOADING
# =====================================================

# NOTE:
# .env is already loaded in main.py via load_dotenv()
# So we just read from os.environ here


# =====================================================
# 🔹 LLM PROVIDER (LOCKED TO GROQ)
# =====================================================

# options: "groq"
LLM_PROVIDER = "groq"


# =====================================================
# 🔹 GROQ CONFIG
# =====================================================

# Required
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Please define it in your environment or .env file."
    )

# Model options:
# - llama-3.1-8b-instant  (fast, cheap, good)
# - llama-3.1-70b-versatile (better quality, slower)
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.1-8b-instant"
)


# =====================================================
# 🔹 RAG / LLM SETTINGS
# =====================================================

# Generation behavior
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.2))
LLM_MAX_TOKENS = os.getenv("LLM_MAX_TOKENS")
LLM_MAX_TOKENS = int(LLM_MAX_TOKENS) if LLM_MAX_TOKENS else None

# Timeout (seconds)
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 60))


# =====================================================
# 🔹 EMBEDDING SETTINGS
# =====================================================

# MUST match FAISSStore EMBED_DIM
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2"
)

EMBED_DIM = 384


# =====================================================
# 🔹 VECTOR STORE SETTINGS
# =====================================================

# Base directory where all FAISS document stores live
VECTORSTORE_BASE_DIR = os.getenv(
    "VECTORSTORE_BASE_DIR",
    "backend/vectorstores"
)


# =====================================================
# 🔹 DEBUG / LOGGING
# =====================================================

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
