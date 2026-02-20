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
from app.routes import chat, sessions, chat_stream

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
# CORS (Production + Local)
# -------------------------

FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,https://drag-eosin.vercel.app"
)

origins = [origin.strip() for origin in FRONTEND_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
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
app.include_router(chat.router)
app.include_router(chat_stream.router)