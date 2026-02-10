import os

# =====================================================
# 🔹 LLM & MODEL CONFIG
# =====================================================
LLM_PROVIDER = "groq"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

EMBEDDING_PROVIDER = "gemini"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "models/gemini-embedding-001")
EMBED_DIM = 768  # Crucial: Must be 768 for your current FAISS setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =====================================================
# 🔹 CHUNKING & RETRIEVAL CONFIG
# =====================================================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 5

# =====================================================
# 🔹 SETTINGS
# =====================================================
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.2))
_raw_max_tokens = os.getenv("LLM_MAX_TOKENS")
LLM_MAX_TOKENS = int(_raw_max_tokens) if _raw_max_tokens else None
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 60))

# =====================================================
# 🔹 VECTOR STORE SETTINGS
# =====================================================
# This was missing from your core/config.py, which caused the error!
VECTORSTORE_BASE_DIR = os.getenv(
    "VECTORSTORE_BASE_DIR", 
    os.path.join(os.getcwd(), "vectorstores")
)

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# =====================================================
# 🔹 MCP SETTINGS
# =====================================================
MCP_ENABLED = os.getenv("MCP_ENABLED", "false").lower() == "true"
MCP_SERVER_URLS = os.getenv("MCP_SERVER_URLS", "").split(",") if MCP_ENABLED else []
