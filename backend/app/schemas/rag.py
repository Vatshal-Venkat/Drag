from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    session_id: str
    query: str
    top_k: int = 8
    document_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    compare_mode: bool = False
    use_human_feedback: bool = True

class QueryResponse(BaseModel):
    answer: str
