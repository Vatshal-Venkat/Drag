from typing import List, Dict, Tuple

# ==================================================
# DOCUMENT CONTEXT TRIMMING (UNCHANGED LOGIC)
# ==================================================

def trim_context(contexts: List[Dict], max_chars: int = 6000) -> Tuple[List[Dict], List[str]]:
    """
    Phase-2 ReAct context trimming:
    - Prefer high-confidence chunks
    - Stop on diminishing returns
    """

    trimmed = []
    total_chars = 0
    used_sources = set()

    contexts = sorted(
        contexts,
        key=lambda c: float(
            c.get("final_score", c.get("confidence", 0.0))
        ),
        reverse=True,
    )

    last_score = None

    for c in contexts:
        text = c.get("text", "")
        score = float(c.get("final_score", c.get("confidence", 0.0)))

        if last_score is not None and last_score - score > 0.4:
            break

        length = len(text)

        if total_chars + length > max_chars:
            break

        trimmed.append(c)
        used_sources.add(c.get("source", "unknown"))
        total_chars += length
        last_score = score

    return trimmed, list(used_sources)


# ==================================================
# CONVERSATION MESSAGE TRIMMING (NEW)
# ==================================================

def estimate_message_length(message: Dict) -> int:
    """
    Rough token-safe approximation using character length.
    """
    return len(message.get("content", ""))


def trim_messages(
    messages: List[Dict],
    *,
    max_chars: int = 8000,
    preserve_system: bool = True,
) -> List[Dict]:
    """
    Trims conversation messages from the oldest forward,
    keeping recent turns within max_chars limit.

    - Preserves system messages if requested.
    - Ensures newest user/assistant turns survive.
    """

    if not messages:
        return messages

    system_messages = []
    non_system_messages = []

    for m in messages:
        if preserve_system and m.get("role") == "system":
            system_messages.append(m)
        else:
            non_system_messages.append(m)

    trimmed = []
    total_chars = 0

    # Iterate from newest backward
    for m in reversed(non_system_messages):
        length = estimate_message_length(m)

        if total_chars + length > max_chars:
            break

        trimmed.append(m)
        total_chars += length

    trimmed.reverse()

    return system_messages + trimmed