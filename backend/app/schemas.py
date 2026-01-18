# app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class IngestRequest(BaseModel):
    text: str
    metadata: Optional[dict] = None

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class SourceChunk(BaseModel):
    text: str
    score: float
    source: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
