from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Existing API routes
from app.api import ingest, health, query_stream

# Chat routes
from app.routes import chat, sessions, chat_stream

from app.registry import document_registry

from app.api import documents


app = FastAPI(title="RAG Accelerator")

document_registry.list_documents()

# -------------------------
# CORS (frontend support)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://drag-eosin.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Existing API routes
# -------------------------
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query_stream.router)   # /rag/query/stream

# -------------------------
# Chat routes
# -------------------------
app.include_router(sessions.router)     # /sessions
app.include_router(chat.router)         # /chat/message
app.include_router(chat_stream.router)    # /chat/stream
app.include_router(documents.router)