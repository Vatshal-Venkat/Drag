from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
