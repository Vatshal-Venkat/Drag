from pydantic import BaseModel
from typing import List, Optional


class SourceChunk(BaseModel):
    id: int
    text: str
    source: Optional[str] = None


class Citation(BaseModel):
    sentence: str
    source_ids: List[int]


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    citations: List[Citation]
