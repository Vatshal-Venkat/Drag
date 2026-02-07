# app/core/config.py

import os

# =====================================================
# 🔹 ENV LOADING
# =====================================================
# NOTE: .env is already loaded in main.py via load_dotenv()


# =====================================================
# 🔹 LLM PROVIDER (LOCKED TO GROQ)
# =====================================================

LLM_PROVIDER = "groq"


# =====================================================
# 🔹 GROQ CONFIG
# =====================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Please define it in your environment or .env file."
    )

GROQ_MODEL = os.getenv(
    "GROQ_MODEL", 
    "llama-3.1-8b-instant"
)


# =====================================================
# 🔹 LLM GENERATION SETTINGS
# =====================================================

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.2))

# Fixed typo: changed LL_MAX_TOKENS to a temporary local for parsing
_raw_max_tokens = os.getenv("LLM_MAX_TOKENS")
LLM_MAX_TOKENS = int(_raw_max_tokens) if _raw_max_tokens else None

LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 60))


# =====================================================
# 🔹 EMBEDDING SETTINGS (GEMINI)
# =====================================================

EMBEDDING_PROVIDER = "gemini"

# Using the verified model name from our diagnostic script
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", 
    "models/gemini-embedding-001" 
)

# This 768 is now enforced in embeddings.py via output_dimensionality
EMBED_DIM = 768

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. "
        "Please define it in your environment or .env file."
    )


# =====================================================
# 🔹 VECTOR STORE SETTINGS
# =====================================================

# Ensures vectorstores are created relative to the backend execution folder
VECTORSTORE_BASE_DIR = os.getenv(
    "VECTORSTORE_BASE_DIR", 
    os.path.join(os.getcwd(), "vectorstores")
)


# =====================================================
# 🔹 DEBUG / LOGGING
# =====================================================

DEBUG = os.getenv("DEBUG", "false").lower() == "true"