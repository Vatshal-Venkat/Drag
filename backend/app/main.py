from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# Existing API routes
# -------------------------
from app.api import ingest, health, query_stream, documents

# -------------------------
# Chat routes
# -------------------------
from app.routes import sessions, chat_stream

# -------------------------
# Registry
# -------------------------
from app.registry import document_registry

# -------------------------
# MCP
# -------------------------
from app.tools.tool_registry import register_mcp_tools
from app.core.config import MCP_ENABLED


app = FastAPI(title="RAG Accelerator")

# -------------------------
# MCP startup hook
# -------------------------
if MCP_ENABLED:
    register_mcp_tools()

# -------------------------
# CORS (Local + Production)
# -------------------------

# Explicitly allow local dev + deployed frontend
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://drag-eosin.vercel.app",
]

# Optional: allow preview vercel deployments
ALLOWED_ORIGIN_REGEX = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
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
app.include_router(query_stream.router)
app.include_router(documents.router)

# -------------------------
# Chat APIs
# -------------------------
app.include_router(sessions.router)
app.include_router(chat_stream.router)