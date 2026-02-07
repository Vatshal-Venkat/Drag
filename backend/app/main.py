from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# Existing API routes
# -------------------------
from app.api import ingest, health, query_stream, documents

# -------------------------
# Chat routes
# -------------------------
from app.routes import chat, sessions, chat_stream

# -------------------------
# Registry
# -------------------------
from app.registry import document_registry

app = FastAPI(title="RAG Accelerator")

# -------------------------
# CORS (Frontend support)
# -------------------------
# We keep the local origins and add your deployed Vercel URL
origins = [
    "https://drag-eosin.vercel.app",  # Production
    "http://localhost:5173",          # Local Vite default
    "http://127.0.0.1:5173",          # Local IP default
    "http://localhost:3000",          # Potential alternative local port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False, # Set to True to support session cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Health & Ingestion APIs
# -------------------------
app.include_router(health.router)
app.include_router(ingest.router)

# -------------------------
# RAG APIs
# -------------------------
app.include_router(query_stream.router)   # /rag/query/stream
app.include_router(documents.router)      # /documents

# -------------------------
# Chat APIs
# -------------------------
app.include_router(sessions.router)       # /sessions
app.include_router(chat.router)           # /chat/message
app.include_router(chat_stream.router)    # /chat/stream