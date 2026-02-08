from typing import List, Dict, Generator

from app.core.session_manager import session_manager

from app.agents.planner_agent import plan_next_steps
from app.tools.tool_registry import get_tool

from app.services.generator import stream_answer, _stream_llm
from app.utils.context_trimmer import trim_context
from app.registry.document_registry import list_documents


CHAT_PROMPT = (
    "You are a friendly, helpful AI assistant.\n"
    "Respond naturally and conversationally.\n"
    "Do not mention internal systems or documents.\n"
)


def execute_chat(
    *,
    session_id: str,
    user_text: str,
) -> Generator[str, None, None]:
    """
    Unified Agentic RAG execution core.
    Yields raw tokens (no SSE / HTTP formatting).
    """

    session = session_manager.get_session(session_id)
    if session is None:
        yield "[ERROR] Session not found"
        return

    session_manager.append_message(
        session_id=session_id,
        role="user",
        content=user_text,
    )

    plan_obj = plan_next_steps(
        session_id=session_id,
        user_query=user_text,
    )

    actions = plan_obj.get("actions", [])
    plan = [a["name"] for a in actions]

    # --------------------------------------------------
    # CHAT-ONLY PATH
    # --------------------------------------------------

    if plan == ["chat"]:
        prompt = CHAT_PROMPT + "\nUser: " + user_text + "\nAssistant:"
        for token in _stream_llm(prompt):
            yield token
        return

    # --------------------------------------------------
    # AGENTIC EXECUTION
    # --------------------------------------------------

    active_docs = session_manager.get_active_documents(session_id)
    document_id = active_docs[0] if active_docs else None

    retrieved_contexts: List[Dict] = []
    reranked_contexts: List[Dict] = []
    tool_observations: List[Dict] = []

    for step in actions:
        name = step.get("name")
        params = step.get("params", {})

        if name == "generate":
            break  # explicit terminator

        tool = get_tool(name)
        if not tool:
            continue

        try:
            result = tool(
                query=user_text,
                document_id=document_id,
                **params,
            )

            if name == "retrieve":
                retrieved_contexts = result
            elif name == "rerank":
                if retrieved_contexts and not retrieved_contexts[0].get("_suggest_rerank", True):
                    tool_observations.append({
                        "tool": "rerank",
                        "result": "skipped (high-confidence retrieval)",
                    })
                    continue

                reranked_contexts = result


            tool_observations.append({
                "tool": name,
                "result": "ok",
            })

        except Exception as e:
            tool_observations.append({
                "tool": name,
                "error": str(e),
            })

    base_contexts = reranked_contexts or retrieved_contexts

    context_blocks, used_docs = trim_context(
        base_contexts,
        max_chars=6000,
    )

    documents_exist = len(list_documents()) > 0

    onboarding_message = ""
    if not context_blocks:
        onboarding_message = (
            "I couldn’t find anything relevant in your uploaded documents.\n\n"
            if documents_exist
            else
            "I don’t see any documents uploaded yet.\n\n"
        )

    collected_tokens: List[str] = []

    for token in stream_answer(
        query=user_text,
        contexts=context_blocks,
        observations=[
            {"step": "plan", "value": plan},
            {"step": "documents_used", "value": used_docs},
            {"step": "tools", "value": tool_observations},
        ],
    ):
        collected_tokens.append(token)
        yield token

    full_answer = onboarding_message + "".join(collected_tokens)

    if full_answer.strip():
        session_manager.append_message(
            session_id=session_id,
            role="assistant",
            content=full_answer.strip(),
        )
