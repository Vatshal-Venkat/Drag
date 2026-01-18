from typing import List, Dict, Iterator
import re

from app.config import LLM_PROVIDER
from app.llm.ollama import stream_ollama
from app.llm.gemini import stream_gemini


def _build_context(contexts: List[Dict]) -> str:
    """
    Build source-grounded context block.
    """
    lines = []
    for c in contexts:
        page = f"(page {c['page']})" if c.get("page") else ""
        lines.append(
            f"[SOURCE {c['id']}] {c['text']} {page}"
        )
    return "\n\n".join(lines)


def _stream_llm(prompt: str) -> Iterator[str]:
    """
    Dispatch streaming call based on provider.
    """
    if LLM_PROVIDER == "ollama":
        return stream_ollama(prompt)

    if LLM_PROVIDER == "gemini":
        return stream_gemini(prompt)

    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def stream_answer(query: str, contexts: List[Dict]) -> Iterator[str]:
    """
    Streams answer tokens from selected LLM.
    """

    context_block = _build_context(contexts)

    prompt = f"""
You are a strict RAG assistant.

Rules:
- Use ONLY the provided sources.
- Every factual sentence must be grounded in sources.
- Do NOT hallucinate facts.
- Keep answers concise and precise.

Sources:
{context_block}

Question:
{query}

Answer:
""".strip()

    for token in _stream_llm(prompt):
        yield token


def generate_sentence_citations(
    full_answer: str,
    contexts: List[Dict]
) -> List[Dict]:
    """
    Map each sentence → supporting sources with confidence.
    """

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", full_answer)
        if s.strip()
    ]

    citations = []

    for sentence in sentences:
        matched_sources = []

        # naive lexical grounding
        for ctx in contexts:
            if ctx["text"][:150].lower() in sentence.lower():
                matched_sources.append(ctx)

        # fallback: highest-confidence sources
        if not matched_sources:
            matched_sources = sorted(
                contexts,
                key=lambda x: x["confidence"],
                reverse=True
            )[:2]

        avg_conf = (
            sum(s["confidence"] for s in matched_sources) / len(matched_sources)
            if matched_sources else 0.0
        )

        citations.append({
            "sentence": sentence,
            "confidence": round(avg_conf, 4),
            "sources": [
                {
                    "id": s["id"],
                    "source": s["source"],
                    "page": s.get("page"),
                    "confidence": s["confidence"],
                }
                for s in matched_sources
            ],
        })

    return citations
