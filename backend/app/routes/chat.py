from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.schemas.session import ChatRequest
from app.agents.chat_executor import execute_chat

router = APIRouter(prefix="/chat", tags=["agentic-chat"])


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    def event_generator():
        for token in execute_chat(
            session_id=payload.session_id,
            user_text=payload.user_text,
        ):
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
