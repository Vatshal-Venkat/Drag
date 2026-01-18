from typing import List, Dict, Iterator
from openai import OpenAI
from app.config import OPENAI_API_KEY, LLM_MODEL
import re

client = OpenAI(api_key=OPENAI_API_KEY)


def _build_context(contexts: List[Dict]) -> str:
    lines = []
    for c in contexts:
        page = f"(page {c['page']})" if c.get("page") else ""
        lines.append(
            f"[SOURCE {c['id']}] {c['text']} {page}"
        )
    return "\n\n".join(lines)


def stream_answer(query: str, contexts: List[Dict]) -> Iterator[str]:
    """
    Stream raw tokens ONLY.
    Citations handled after generation.
    """

    context_block = _build_context(contexts)

    prompt = f"""
You are a strict RAG assistant.

Rules:
- Use ONLY the provided sources.
- Every factual sentence must be grounded in sources.
- Do NOT invent citations.

Sources:
{context_block}

Question:
{query}

Answer:
"""

    stream = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def generate_sentence_citations(
    full_answer: str,
    contexts: List[Dict]
) -> List[Dict]:
    """
    Maps each sentence → best supporting sources.
    """

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", full_answer)
        if s.strip()
    ]

    citations = []

    for sentence in sentences:
        matched_sources = []

        for ctx in contexts:
            if ctx["text"][:200].lower() in sentence.lower():
                matched_sources.append(ctx)

        # fallback: top-confidence sources
        if not matched_sources:
            matched_sources = sorted(
                contexts,
                key=lambda x: x["confidence"],
                reverse=True
            )[:2]

        citations.append({
            "sentence": sentence,
            "sources": [
                {
                    "id": s["id"],
                    "source": s["source"],
                    "page": s.get("page"),
                    "confidence": s["confidence"],
                }
                for s in matched_sources
            ],
            "confidence": round(
                sum(s["confidence"] for s in matched_sources)
                / len(matched_sources),
                4,
            ),
        })

    return citations
