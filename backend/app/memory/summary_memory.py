import os
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MEMORY_DIR = os.path.join(BASE_DIR, "memory_store")
MEMORY_FILE = os.path.join(MEMORY_DIR, "summary.txt")

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
    lines = []

    if previous_summary:
        lines.append(previous_summary.strip())

    lines.append(f"User intent: {user_query.strip()}")
    lines.append(f"Key answer: {assistant_answer.strip()[:400]}")

    new_summary = "\n".join(lines[-6:])
    save_summary(new_summary)
    return new_summary


def should_update_summary(
    user_query: str,
    assistant_answer: str,
) -> bool:
    if not assistant_answer:
        return False

    if len(assistant_answer.strip()) < 150:
        return False

    return True