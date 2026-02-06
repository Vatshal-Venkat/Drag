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

# Initialize document registry at startup

#document_registry.list_documents()

# -------------------------
# CORS (Frontend support)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://drag-eosin.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
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
