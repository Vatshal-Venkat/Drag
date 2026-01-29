from typing import List, Dict, Iterator
import re
import textwrap

from app.config import LLM_PROVIDER
from groq import Groq

# -------------------------------------------------
# ACTIVE LLM: Groq (LLaMA 3)
# -------------------------------------------------

_groq_client = Groq()
GROQ_MODEL = "llama3-70b-8192"


# -------------------------
# Context formatting
# -------------------------

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


# -------------------------
# STREAMING LLM (USED ONLY BY /query/stream)
# -------------------------

def _stream_llm(prompt: str) -> Iterator[str]:
    stream = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
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
        ],
        temperature=0.3,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


# -------------------------
# NON-STREAMING LLM (USED BY /chat/message)
# -------------------------

def _call_llm(prompt: str) -> str:
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
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
        ],
        temperature=0.3,
        stream=False,
    )

    return response.choices[0].message.content.strip()


# -------------------------
# Answer generation (STREAMING)
# -------------------------

def stream_answer(query: str, contexts: List[Dict]) -> Iterator[str]:
    if not contexts:
        yield "Based on the provided documents, no relevant information was found."
        return

    context_block = _build_context(contexts)

    system_prompt = """You are a strict resume analysis assistant.

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

    for token in _stream_llm(full_prompt):
        yield token


# -------------------------
# Answer generation (NON-STREAMING)
# -------------------------

def generate_answer(prompt: str) -> str:
    """
    Safe synchronous LLM call.
    Used by /chat/message.
    """
    return _call_llm(prompt)


# -------------------------
# Sentence-level citations
# -------------------------

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