from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    top_k: int = Field(5, ge=1, le=20)
    document_id: str = Field(..., description="Document to query")


class QueryResponse(BaseModel):
    answer: str
