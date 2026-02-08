def trim_context(contexts, max_chars=6000):
    """
    Phase-2 ReAct context trimming:
    - Prefer high-confidence chunks
    - Stop on diminishing returns
    """

    trimmed = []
    total_chars = 0
    used_sources = set()

    # 🔹 ReAct: highest-value chunks first
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

        # 🔹 ReAct: diminishing returns cutoff
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
