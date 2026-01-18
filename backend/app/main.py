from fastapi import FastAPI
from app.api import ingest, health, query_stream
from backend.app.api import query_stream
from app.api import ingest

app = FastAPI(title="RAG Accelerator")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query_stream.router)
app.include_router(query_stream.router)


app.include_router(ingest.router)

