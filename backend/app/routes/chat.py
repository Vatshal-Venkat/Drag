from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.schemas.session import ChatRequest
from app.core.session_manager import session_manager
from app.services.retriever import retrieve
from app.services.generator import _stream_llm
from app.prompts import load_prompt
from app.utils.context_trimmer import trim_context
from app.registry.document_registry import list_documents

router = APIRouter(prefix="/chat", tags=["chat"])

# Prompts
RAG_QA_PROMPT = load_prompt("rag_qa_prompt.txt")
RAG_SUMMARY_PROMPT = load_prompt("rag_summary_prompt.txt")
CHAT_PROMPT = (
    "You are a friendly, helpful AI assistant.\n"
    "Respond naturally and conversationally.\n"
    "Do not mention internal systems or documents.\n"
)

# --------------------------------------------------
# Intent helpers
# --------------------------------------------------

def is_summary_intent(text: str) -> bool:
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


def is_greeting_or_smalltalk(text: str) -> bool:
    t = text.strip().lower()
    return t in {"hi", "hello", "hey", "yo", "sup", "what"}


def is_personal_query(text: str) -> bool:
    keywords = [
        "my resume",
        "my projects",
        "my skills",
        "my experience",
        "about me",
        "my background",
    ]
    q = text.lower()
    return any(k in q for k in keywords)


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    """
    Unified Chat + RAG streaming endpoint with document isolation.
    """

    # 1️⃣ Validate session
    session = session_manager.get_session(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2️⃣ Append user message
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

    # --------------------------------------------------
    # CHAT MODE (no retrieval)
    # --------------------------------------------------
    if is_greeting_or_smalltalk(payload.user_text):
        prompt = CHAT_PROMPT + "\nUser: " + payload.user_text + "\nAssistant:"

        def event_generator():
            for token in _stream_llm(prompt):
                yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # --------------------------------------------------
    # RAG MODE (with document isolation)
    # --------------------------------------------------

    document_id = None
    if is_personal_query(payload.user_text):
        document_id = session.get("active_document_id")

    contexts = retrieve(
        payload.user_text,
        k=5,
        document_id=document_id,
    )

    context_blocks, used_docs = trim_context(contexts, max_chars=6000)
    context_text = "\n".join(c["text"] for c in context_blocks)

    synthesis_hint = (
        "\n\nThe context may include multiple sections. "
        "Use only the parts relevant to the question."
    )

    context_note = ""
    onboarding_message = ""

    # 🔧 FIX: distinguish "no docs exist" vs "no relevant chunks"
    documents_exist = len(list_documents()) > 0

    if not context_text.strip():
        context_note = (
            "\n\nIf no relevant context is available, "
            "respond briefly and conversationally without factual claims."
        )

        if documents_exist:
            onboarding_message = (
                "I couldn’t find anything relevant in your uploaded documents "
                "for this question."
            )
        else:
            onboarding_message = (
                "I don’t see any documents uploaded yet. "
                "You can upload a file below if you want me to answer based on it."
            )

    # 5️⃣ Choose prompt
    if is_summary_intent(payload.user_text):
        prompt = RAG_SUMMARY_PROMPT.format(
            context=context_text + synthesis_hint
        )
    else:
        prompt = RAG_QA_PROMPT.format(
            memory=memory_text,
            context=context_text + synthesis_hint + context_note,
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

            if onboarding_message and full_answer:
                full_answer = onboarding_message + "\n\n" + full_answer

            # Inline citations
            paragraphs = [p.strip() for p in full_answer.split("\n\n") if p.strip()]
            cited_paragraphs = []

            for idx, para in enumerate(paragraphs):
                if idx < len(context_blocks):
                    src = context_blocks[idx]
                    citation = f"(Source: {src['source']}, page {src['page']})"
                    cited_paragraphs.append(f"{para}\n{citation}")
                else:
                    cited_paragraphs.append(para)

            final_answer = "\n\n".join(cited_paragraphs)

            if final_answer:
                session_manager.append_message(
                    session_id=payload.session_id,
                    role="assistant",
                    content=final_answer,
                )

            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
