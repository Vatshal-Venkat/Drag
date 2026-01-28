from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Existing API routes (keep these)
from app.api import ingest, health, query_stream

# NEW ChatGPT-style routes
from app.routes import chat, sessions


app = FastAPI(title="RAG Accelerator")

# -------------------------
# CORS (frontend support)
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Existing API routes
# -------------------------

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query_stream.router)

# -------------------------
# ChatGPT-style routes
# -------------------------

app.include_router(sessions.router)   # /sessions
app.include_router(chat.router)       # /chat/message