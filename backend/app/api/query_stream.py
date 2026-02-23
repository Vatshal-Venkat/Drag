from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import Any

from app.schemas.rag import QueryRequest
from app.core.conversation_engine import ConversationEngine

router = APIRouter(prefix="/rag")

engine = ConversationEngine()


# --------------------------------------------------
# JSON SAFE HELPER
# --------------------------------------------------

def make_json_safe(obj: Any):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj


# --------------------------------------------------
# UNIFIED STREAM ENDPOINT
# --------------------------------------------------

@router.post("/query/stream")
def query_rag_stream(req: QueryRequest):

    if not req.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required"
        )

    def event_generator():

        for event in engine.stream(
            session_id=req.session_id,
            query=req.query,
            compare_mode=req.compare_mode,
            document_ids=req.document_ids,
            top_k=req.top_k,
            use_human_feedback=req.use_human_feedback,
        ):

            if event.get("type") == "error":
                yield f"data: {json.dumps(event)}\n\n"
                yield "data: [DONE]\n\n"
                return

            yield f"data: {json.dumps(make_json_safe(event))}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )