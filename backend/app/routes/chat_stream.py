from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.schemas.session import ChatRequest
from app.agents.chat_executor import execute_chat

router = APIRouter(prefix="/chat", tags=["agentic-chat-stream"])


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    def sse_generator():
        for token in execute_chat(
            session_id=payload.session_id,
            user_text=payload.user_text,
        ):
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
