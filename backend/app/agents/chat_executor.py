from typing import List, Dict, Generator, Any
import re
import json

from app.core.session_manager import session_manager
from app.tools.tool_registry import get_tool, list_tools
from app.core.llms import planner_llm, generator_llm
from app.utils.context_trimmer import trim_context
from app.registry.document_registry import list_documents


# ==================================================
# CONFIG
# ==================================================

MAX_REACT_STEPS = 5

REACT_SYSTEM_PROMPT = """
You are an advanced reasoning AI agent.

You MUST use this exact format:

Thought: <your reasoning>
Action: <tool name OR "final">
Action Input: <valid JSON>

Available tools:
{tools}

When ready to answer:

Thought: I now know the final answer
Action: final
Action Input: {{"answer": "<final answer here>"}}

Rules:
- Do not skip format.
- Do not invent tools.
- Use tools when relevant.
- Do not output anything outside this format.
"""


CHAT_PROMPT = (
    "You are a friendly, helpful AI assistant.\n"
    "Respond naturally and conversationally.\n"
    "Do not mention internal systems or documents.\n"
)


# ==================================================
# ACKNOWLEDGEMENT GUARD
# ==================================================

_ACK_PATTERNS = [
    r"^thanks?$",
    r"^thank you$",
    r"^thx$",
    r"^ok$",
    r"^okay$",
    r"^fine$",
    r"^got it$",
    r"^cool$",
    r"^great$",
    r"^very good$",
    r"^nice$",
    r"^yes$",
    r"^👍$",
]


def _is_acknowledgement(text: str) -> bool:
    text = text.strip().lower()
    return any(re.match(p, text) for p in _ACK_PATTERNS)


# ==================================================
# ROUTER — SHOULD USE REACT?
# ==================================================

def _should_use_react(session_id: str, user_text: str) -> bool:
    active_docs = session_manager.get_active_documents(session_id)

    # No documents loaded → no need for ReACT
    if not active_docs:
        return False

    # Very short / casual input → no ReACT
    if len(user_text.strip().split()) < 4:
        return False

    # If query looks like greeting or unclear
    if user_text.lower() in ["hello", "hi", "hey"]:
        return False

    return True


# ==================================================
# REACT PARSER
# ==================================================

def _parse_react_output(text: str) -> Dict[str, Any]:
    thought_match = re.search(r"Thought:(.*)", text)
    action_match = re.search(r"Action:(.*)", text)
    input_match = re.search(r"Action Input:(.*)", text, re.DOTALL)

    thought = thought_match.group(1).strip() if thought_match else ""
    action = action_match.group(1).strip() if action_match else ""
    raw_input = input_match.group(1).strip() if input_match else "{}"

    try:
        action_input = json.loads(raw_input)
    except Exception:
        action_input = {}

    return {
        "thought": thought,
        "action": action,
        "action_input": action_input,
    }


# ==================================================
# MAIN EXECUTOR
# ==================================================

def execute_chat(
    *,
    session_id: str,
    user_text: str,
) -> Generator[str, None, None]:

    session = session_manager.get_session(session_id)
    if session is None:
        yield "[ERROR] Session not found"
        return

    # ----------------------------------------
    # ACK SHORT-CIRCUIT
    # ----------------------------------------

    if _is_acknowledgement(user_text):
        reply = "You're welcome 🙂"
        yield reply
        session_manager.append_message(
            session_id=session_id,
            role="assistant",
            content=reply,
        )
        return

    session_manager.append_message(
        session_id=session_id,
        role="user",
        content=user_text,
    )

    memory_snapshot = session_manager.get_recent_messages(
        session_id=session_id,
        limit=5,
    )

    # ==================================================
    # CHAT MODE (No ReACT)
    # ==================================================

    if not _should_use_react(session_id, user_text):

        chat_messages = [{"role": "system", "content": CHAT_PROMPT}]
        chat_messages.extend(memory_snapshot)

        collected = ""

        for token in generator_llm(chat_messages, stream=True):
            collected += token
            yield token

        follow_up = "\n\nDo you want me to explain more?"
        yield follow_up
        collected += follow_up

        session_manager.append_message(
            session_id=session_id,
            role="assistant",
            content=collected.strip(),
        )

        return

    # ==================================================
    # REACT MODE
    # ==================================================

    tools = list_tools()
    tools_str = "\n".join(f"- {t}" for t in tools)

    system_prompt = REACT_SYSTEM_PROMPT.format(tools=tools_str)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory_snapshot)

    active_docs = session_manager.get_active_documents(session_id)
    document_id = active_docs[0] if active_docs else None

    contexts: List[Dict] = []
    final_answer = None

    for _ in range(MAX_REACT_STEPS):

        response = planner_llm(messages, stream=False)

        parsed = _parse_react_output(response)
        action = parsed["action"]
        action_input = parsed["action_input"]

        # FINAL
        if action == "final":
            final_answer = action_input.get("answer", "")
            break

        tool = get_tool(action)

        if not tool:
            observation = f"Tool '{action}' not available."
        else:
            try:
                result = tool(
                    query=user_text,
                    document_id=document_id,
                    **action_input,
                )
                observation = result

                if action == "retrieve":
                    contexts = result

            except Exception as e:
                observation = f"Tool error: {str(e)}"

        session_manager.add_observation(
            session_id=session_id,
            step=action,
            value="ok",
        )

        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": f"Observation: {str(observation)}",
        })

    if not final_answer:
        final_answer = "I couldn't complete reasoning within allowed steps."

    # ==================================================
    # CONTEXT TRIMMING
    # ==================================================

    context_blocks, _ = trim_context(
        contexts,
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

    # ==================================================
    # FINAL STREAM
    # ==================================================

    final_messages = [
        {"role": "system", "content": CHAT_PROMPT},
        {"role": "user", "content": final_answer},
    ]

    collected_tokens: List[str] = []

    for token in generator_llm(final_messages, stream=True):
        collected_tokens.append(token)
        yield token

    follow_up = "\n\nDo you want me to explain more?"
    yield follow_up
    collected_tokens.append(follow_up)

    full_answer = onboarding_message + "".join(collected_tokens)

    session_manager.append_message(
        session_id=session_id,
        role="assistant",
        content=full_answer.strip(),
    )