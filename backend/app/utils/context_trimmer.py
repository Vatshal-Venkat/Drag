def trim_context(contexts, max_chars=6000):
    """
    Trims context conservatively based on character count.
    Preserves source metadata for citation mapping.
    """

    trimmed = []
    total_chars = 0

    for c in contexts:
        text = c.get("text", "")
        length = len(text)

        if total_chars + length > max_chars:
            break

        trimmed.append({
            "text": text,
            "source": c.get("source", "unknown"),
            "page": c.get("page"),
        })

        total_chars += length

    return trimmed, len(trimmed)
