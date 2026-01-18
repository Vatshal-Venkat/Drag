def chunk_text(text: str, size: int = 500, overlap: int = 100):
    """
    Splits text into overlapping chunks (character-based, safe version).
    """

    if not text or size <= overlap:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += size - overlap

    return chunks
