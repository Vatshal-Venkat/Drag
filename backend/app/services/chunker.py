# backend/app/services/chunker.py

import re
from typing import List


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _is_heading(paragraph: str) -> bool:
    if len(paragraph) < 120 and paragraph.isupper():
        return True
    if paragraph.strip().endswith(":"):
        return True
    return False


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> List[str]:
    """
    Improved semantic-aware chunking.
    - Paragraph-based
    - Preserves section headers
    - Soft size limit
    """

    if not text or size <= overlap:
        return []

    paragraphs = _split_paragraphs(text)

    chunks = []
    current_chunk = ""
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        # If heading, force new chunk boundary
        if _is_heading(para) and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n"
            current_len = len(current_chunk)
            continue

        if current_len + para_len <= size:
            current_chunk += para + "\n\n"
            current_len += para_len
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # overlap by last portion
            overlap_text = current_chunk[-overlap:] if overlap < len(current_chunk) else ""
            current_chunk = overlap_text + "\n" + para + "\n\n"
            current_len = len(current_chunk)

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks