from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.session import ChatRequest
from app.core.session_manager import session_manager
from app.services.retriever import retrieve
from app.services.generator import stream_answer
from app.prompts import load_prompt

router = APIRouter(prefix="/chat", tags=["chat-stream"])

RAG_PROMPT = load_prompt("rag_prompt.txt")


def sse_event_generator(payload: ChatRequest):
    """
    SSE generator yielding token-level events
    """

    # 1️⃣ Validate session
    session = session_manager.get_session(payload.session_id)
    if session is None:
        yield "event: error\ndata: Session not found\n\n"
        return

    # -------------------------------------------------
    # 🔹 MULTI-DOCUMENT SESSION MEMORY (NEW)
    # -------------------------------------------------
    if "active_documents" not in session:
        session["active_documents"] = set()

    # 2️⃣ Save user message
    session_manager.append_message(
        session_id=payload.session_id,
        role="user",
        content=payload.user_text,
    )

    # 3️⃣ Build memory (last N messages)
    memory_messages = session["messages"][-10:]
    memory_text = "\n".join(
        f'{m["role"]}: {m["content"]}' for m in memory_messages
    )

    # -------------------------------------------------
    # 🔹 Multi-document retrieval (session-aware)
    # -------------------------------------------------
    contexts = []

    if session["active_documents"]:
        # Query across all active documents in this session
        for doc_id in session["active_documents"]:
            contexts.extend(
                retrieve(
                    query=payload.user_text,
                    k=2,
                    document_id=doc_id,
                )
            )
    else:
        # Fallback: global/default retrieval
        contexts = retrieve(
            query=payload.user_text,
            k=5,
        )

    # Track which documents contributed
    for c in contexts:
        src = c.get("source")
        if src:
            session["active_documents"].add(src)

    context_text = "\n".join(
        c.get("text", "") for c in contexts
    )

    # 4️⃣ Final prompt
    prompt = RAG_PROMPT.format(
        memory=memory_text,
        context=context_text,
        question=payload.user_text,
    )

    # 5️⃣ Stream tokens
    full_answer = []

    for token in stream_answer(payload.user_text, contexts):
        full_answer.append(token)
        yield f"data: {token}\n\n"

    # 6️⃣ Save assistant message
    session_manager.append_message(
        session_id=payload.session_id,
        role="agent",
        content="".join(full_answer),
    )

    # 7️⃣ End stream
    yield "event: done\ndata: [DONE]\n\n"


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    """
    SSE endpoint for ChatGPT-style streaming
    """

    return StreamingResponse(
        sse_event_generator(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
