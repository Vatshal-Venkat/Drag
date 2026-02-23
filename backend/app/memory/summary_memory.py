import os
from typing import Optional

from app.core.llms import summarizer_llm

# --------------------------------------------------
# BASE PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROMPT_PATH = os.path.join(BASE_DIR, "rag_summary_prompt.txt")


# --------------------------------------------------
# LOAD SUMMARY PROMPT TEMPLATE
# --------------------------------------------------

def _load_summary_prompt() -> str:
    if not os.path.exists(PROMPT_PATH):
        raise FileNotFoundError(
            "rag_summary_prompt.txt not found. Summary system requires it."
        )

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------
# LLM-BASED SUMMARY UPDATE
# --------------------------------------------------

def update_summary(
    previous_summary: str,
    user_query: str,
    assistant_answer: str,
) -> str:
    """
    Uses LLM to intelligently compress conversation memory.
    """

    if not assistant_answer.strip():
        return previous_summary or ""

    prompt_template = _load_summary_prompt()

    combined_context = f"""
Previous Summary:
{previous_summary}

New Interaction:
User: {user_query}
Assistant: {assistant_answer}
""".strip()

    final_prompt = prompt_template.replace(
        "{context}",
        combined_context
    )

    messages = [
        {
            "role": "system",
            "content": "You are a memory compression engine."
        },
        {
            "role": "user",
            "content": final_prompt
        }
    ]

    new_summary = summarizer_llm(messages)

    # Safety fallback
    if not new_summary or len(new_summary.strip()) < 20:
        return previous_summary or ""

    # Hard cap to avoid runaway summary growth
    return new_summary.strip()[:3000]


# --------------------------------------------------
# SUMMARY UPDATE CONTROL
# --------------------------------------------------

def should_update_summary(
    user_query: str,
    assistant_answer: str,
) -> bool:

    if not assistant_answer:
        return False

    if len(assistant_answer.strip()) < 200:
        return False

    if len(user_query.strip()) < 5:
        return False

    return True