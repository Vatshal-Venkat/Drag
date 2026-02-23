from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.schemas.session import ChatRequest
from app.core.conversation_engine import ConversationEngine

router = APIRouter(prefix="/chat", tags=["agentic-chat-stream"])

engine = ConversationEngine()


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj


@router.post("/stream")
def chat_stream(payload: ChatRequest):

    if not payload.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required"
        )

    def sse_generator():

        for event in engine.stream(
            session_id=payload.session_id,
            query=payload.user_text,
            compare_mode=False,
            document_ids=None,
            top_k=5,
            use_human_feedback=True,
        ):
            yield f"data: {json.dumps(make_json_safe(event))}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )