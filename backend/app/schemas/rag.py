from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    # -------------------------
    # Core query fields
    # -------------------------
    query: str = Field(..., description="User query")
    top_k: int = Field(5, ge=1, le=20)

    # -------------------------
    # Document selection
    # -------------------------
    # Existing single-document support (unchanged)
    document_id: Optional[str] = Field(
        None,
        description="Single document to query (default behavior)"
    )

    # New: multi-document support (for comparison mode)
    document_ids: Optional[List[str]] = Field(
        None,
        description="List of document IDs for comparison queries"
    )

    # -------------------------
    # Feature flags
    # -------------------------
    compare_mode: bool = Field(
        False,
        description="Enable cross-document comparison mode"
    )

    use_human_feedback: bool = Field(
        True,
        description="Whether to apply human-in-the-loop corrections if available"
    )


class QueryResponse(BaseModel):
    answer: str
