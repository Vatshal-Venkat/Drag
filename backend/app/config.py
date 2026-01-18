# app/config.py

# -------- LLM PROVIDER --------
# options: "ollama", "gemini"
LLM_PROVIDER = "ollama"

# -------- OLLAMA CONFIG --------
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"

# -------- GEMINI CONFIG --------
GEMINI_API_KEY = ""  # add later when needed
GEMINI_MODEL = "models/gemini-1.5-flash"

# -------- RAG / LLM SETTINGS --------
LLM_TEMPERATURE = 0.2
LLM_TIMEOUT = 60
