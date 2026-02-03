from typing import List, Dict, Iterator
import re
import textwrap

from app.llm.groq import groq_stream, groq_chat
from app.config import GROQ_MODEL, LLM_TEMPERATURE


# -------------------------------------------------
# Context formatting
# -------------------------------------------------

def _build_context(contexts: List[Dict]) -> str:
    blocks = []

    for i, c in enumerate(contexts, start=1):
        block = f"""
[Source {i}]
Document: {c.get('source', 'unknown')}
Page: {c.get('page', 'N/A')}
Relevance: {round(float(c.get('confidence', 0)), 3)}

Content:
{c.get('text', '').strip()}
"""
        blocks.append(textwrap.dedent(block).strip())

    return "\n\n---\n\n".join(blocks)


# -------------------------------------------------
# STREAMING LLM (Groq)
# -------------------------------------------------

def _stream_llm(prompt: str) -> Iterator[str]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict RAG assistant. "
                "Answer only using the provided context. "
                "Do not hallucinate or assume missing facts."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    for token in groq_stream(
        messages=messages,
        model=GROQ_MODEL,
        temperature=LLM_TEMPERATURE,
    ):
        yield token


# -------------------------------------------------
# Answer generation (STREAMING + INLINE CITATIONS)
# -------------------------------------------------

def stream_answer(query: str, contexts: List[Dict]) -> Iterator[str]:
    if not contexts:
        yield "Based on the provided documents, no relevant information was found."
        return

    # Pre-assign citation IDs
    citation_map = {
        idx + 1: ctx for idx, ctx in enumerate(contexts)
    }

    context_block = _build_context(contexts)

    system_prompt = """You are a strict RAG assistant.

Rules:
1. Use ONLY provided context
2. Do NOT hallucinate
3. If missing info, say so explicitly
"""

    user_prompt = f"""
Context:
{context_block}

Question:
{query}

Answer:
"""

    full_prompt = f"{system_prompt}\n\n{user_prompt}".strip()

    buffer = ""
    sentence_end = re.compile(r"[.!?]\s*$")

    for token in _stream_llm(full_prompt):
        buffer += token
        yield token

        # Emit inline citations at sentence boundaries
        if sentence_end.search(buffer):
            top_sources = sorted(
                citation_map.items(),
                key=lambda x: float(x[1].get("confidence", 0)),
                reverse=True
            )[:2]

            citation_tag = " [" + ",".join(
                f"S{sid}" for sid, _ in top_sources
            ) + "]"

            yield citation_tag
            buffer = ""


# -------------------------------------------------
# NON-STREAMING LLM (chat usage)
# -------------------------------------------------

def generate_answer(prompt: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict RAG assistant. "
                "Answer only using the provided context. "
                "Do not hallucinate or assume missing facts."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    result = groq_chat(
        messages=messages,
        model=GROQ_MODEL,
    )

    return result.choices[0].message.content.strip()


# -------------------------------------------------
# Sentence-level citations (post-processing)
# -------------------------------------------------

def generate_sentence_citations(
    full_answer: str,
    contexts: List[Dict]
) -> List[Dict]:

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", full_answer)
        if s.strip()
    ]

    citations = []

    for sentence in sentences:
        matched_sources = []
        sentence_lower = sentence.lower()

        for ctx in contexts:
            ctx_text = ctx.get("text", "").lower()
            if any(word in ctx_text for word in sentence_lower.split()[:6]):
                matched_sources.append(ctx)

        if not matched_sources:
            matched_sources = sorted(
                contexts,
                key=lambda x: float(x.get("confidence", 0)),
                reverse=True
            )[:2]

        avg_conf = (
            sum(float(s.get("confidence", 0)) for s in matched_sources)
            / len(matched_sources)
            if matched_sources else 0.0
        )

        citations.append({
            "sentence": sentence,
            "confidence": round(avg_conf, 4),
            "sources": [
                {
                    "id": s.get("id"),
                    "source": s.get("source"),
                    "page": s.get("page"),
                    "confidence": float(s.get("confidence", 0)),
                }
                for s in matched_sources
            ],
        })

    return citations
