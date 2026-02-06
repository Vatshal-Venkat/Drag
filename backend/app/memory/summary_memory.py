import os
import json
from typing import Optional

MEMORY_DIR = "backend/memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "summary.json")

os.makedirs(MEMORY_DIR, exist_ok=True)


def load_summary() -> str:
    if not os.path.exists(MEMORY_FILE):
        return ""
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return f.read()


def save_summary(text: str):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write(text)


def update_summary(
    previous_summary: str,
    user_query: str,
    assistant_answer: str,
) -> str:
    """
    VERY light-weight summarizer.
    You can later replace this with an LLM call.
    """

    lines = []

    if previous_summary:
        lines.append(previous_summary.strip())

    lines.append(f"User intent: {user_query.strip()}")
    lines.append(f"Key answer: {assistant_answer.strip()[:400]}")

    new_summary = "\n".join(lines[-6:])  # keep memory small
    save_summary(new_summary)
    return new_summary


# ==================================================
# 🔹 AGENT-FACING HELPERS (ADDITIVE)
# ==================================================

def should_update_summary(
    user_query: str,
    assistant_answer: str,
) -> bool:
    """
    Memory Agent heuristic (cheap + deterministic).
    Planner can override this later.
    """
    return len(assistant_answer.strip()) > 120
