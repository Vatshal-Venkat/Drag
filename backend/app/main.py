from fastapi import FastAPI
from app.api import ingest, query, health

app = FastAPI(title="RAG Accelerator")

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
