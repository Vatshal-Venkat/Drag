from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.schemas.session import ChatRequest
from app.core.session_manager import session_manager
from app.services.retriever import retrieve
from app.services.generator import _stream_llm
from app.prompts import load_prompt
from app.utils.context_trimmer import trim_context

router = APIRouter(prefix="/chat", tags=["chat"])

# RAG prompts
RAG_QA_PROMPT = load_prompt("rag_qa_prompt.txt")
RAG_SUMMARY_PROMPT = load_prompt("rag_summary_prompt.txt")


def is_summary_intent(text: str) -> bool:
    """
    Lightweight intent detection for summary vs Q&A.
    Biased toward Q&A for safety.
    """
    summary_keywords = [
        "summarize",
        "summary",
        "overview",
        "explain the document",
        "give an overview",
        "tl;dr",
        "briefly explain",
        "high level",
    ]

    q = text.lower()
    return any(k in q for k in summary_keywords)


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    """
    RAG-focused, ChatGPT-style streaming chat endpoint (SSE).
    Friendly, explanatory, and grounded in retrieved context.
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

    # 3️⃣ Build short-term memory
    memory_messages = session["messages"][-10:]
    memory_text = "\n".join(
        f'{m["role"]}: {m["content"]}' for m in memory_messages
    )

    # 4️⃣ Always retrieve context (RAG-first)
    contexts = retrieve(payload.user_text, k=5)

    # Token-aware trimming (char-based, model-agnostic)
    context_text, used_docs = trim_context(contexts, max_chars=6000)

    # 🔹 Onboarding + no-context handling
    context_note = ""
    onboarding_message = ""

    if not context_text.strip():
        context_note = (
            "\n\nNote: No relevant documents were retrieved for this query. "
            "If appropriate, respond briefly and conversationally without "
            "introducing factual claims."
        )

        onboarding_message = (
            "I don’t see any documents uploaded yet. "
            "You can upload a file or ask a question about a document, "
            "and I’ll help analyze it."
        )

    # 5️⃣ Choose prompt based on intent
    if is_summary_intent(payload.user_text):
        prompt = RAG_SUMMARY_PROMPT.format(
            context=context_text
        )
    else:
        prompt = RAG_QA_PROMPT.format(
            memory=memory_text,
            context=context_text + context_note,
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

            # 🔹 Prepend onboarding message if needed
            if onboarding_message and full_answer:
                full_answer = onboarding_message + "\n\n" + full_answer

            # 7️⃣ Append grounding confidence line
            if full_answer and used_docs > 0:
                full_answer += (
                    f"\n\n—\nAnswer grounded in "
                    f"{used_docs} retrieved document"
                    f"{'s' if used_docs > 1 else ''}."
                )

            # 8️⃣ Append assistant message ONCE
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
