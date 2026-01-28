from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.schemas.session import ChatRequest, ChatResponse
from app.core.session_manager import session_manager
from app.services.retriever import retrieve
from app.services.generator import generate_answer
from app.prompts import load_prompt

router = APIRouter(prefix="/chat", tags=["chat"])

# Load RAG prompt once at startup
RAG_PROMPT = load_prompt("rag_prompt.txt")


@router.post("/message", response_model=ChatResponse)
def chat_message(payload: ChatRequest):
    """
    ChatGPT-style chat endpoint with session memory + FAISS RAG.
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

    # 3️⃣ Build memory (last N messages)
    memory_messages = session["messages"][-10:]
    memory_text = "\n".join(
        f'{m["role"]}: {m["content"]}' for m in memory_messages
    )

    # 4️⃣ Retrieve context from FAISS
    contexts = retrieve(payload.user_text, k=5)
    context_text = "\n".join(c["text"] for c in contexts)

    # 5️⃣ Build final RAG prompt
    prompt = RAG_PROMPT.format(
        memory=memory_text,
        context=context_text,
        question=payload.user_text,
    )

    # 6️⃣ Generate answer using Groq (LLaMA-3)
    answer = generate_answer(prompt)

    # 7️⃣ Append agent message
    session_manager.append_message(
        session_id=payload.session_id,
        role="agent",
        content=answer,
    )

    return ChatResponse(
        role="agent",
        content=answer,
        timestamp=datetime.utcnow(),
    )