def trim_context(contexts, max_chars=6000):
    """
    Trims context conservatively based on character count.
    Char-based trimming is reliable across tokenizers.
    """
    trimmed = []
    total_chars = 0

    for c in contexts:
        text = c["text"]
        length = len(text)

        if total_chars + length > max_chars:
            break

        trimmed.append(text)
        total_chars += length

    return "\n".join(trimmed), len(trimmed)
