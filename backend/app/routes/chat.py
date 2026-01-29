from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json

from app.schemas.session import ChatRequest
from app.core.session_manager import session_manager
from app.services.retriever import retrieve
from app.services.generator import _stream_llm
from app.prompts import load_prompt

router = APIRouter(prefix="/chat", tags=["chat"])

RAG_PROMPT = load_prompt("rag_prompt.txt")


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    """
    ChatGPT-style streaming chat endpoint (SSE).
    """

    # 1️⃣ Validate session
    session = session_manager.get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2️⃣ Append user message immediately
    session_manager.append_message(
        session_id=payload.session_id,
        role="user",
        content=payload.user_text,
    )

    # 3️⃣ Build memory
    memory_messages = session["messages"][-10:]
    memory_text = "\n".join(
        f'{m["role"]}: {m["content"]}' for m in memory_messages
    )

    # 4️⃣ Retrieve context
    contexts = retrieve(payload.user_text, k=5)
    context_text = "\n".join(c["text"] for c in contexts)

    # 5️⃣ Build RAG prompt
    prompt = RAG_PROMPT.format(
        memory=memory_text,
        context=context_text,
        question=payload.user_text,
    )

    # 6️⃣ Streaming generator
    def event_generator():
        collected = []

        try:
            for token in _stream_llm(prompt):
                collected.append(token)
                yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

        finally:
            full_answer = "".join(collected).strip()

            # 7️⃣ Append assistant message ONCE
            if full_answer:
                session_manager.append_message(
                    session_id=payload.session_id,
                    role="assistant",
                    content=full_answer,
                )

            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )