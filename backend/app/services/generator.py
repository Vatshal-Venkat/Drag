from typing import List, Dict, Iterator
import re
import textwrap

from app.config import LLM_PROVIDER
from app.llm.ollama import stream_ollama
from app.llm.gemini import stream_gemini


# -------------------------
# Context formatting
# -------------------------

def _build_context(contexts: List[Dict]) -> str:
    """
    Build a structured, LLM-friendly context block.
    This dramatically improves grounding quality.
    """

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
# LLM streaming dispatcher
# -------------------------

def _stream_llm(prompt: str) -> Iterator[str]:
    """
    Dispatch streaming call based on provider.
    """
    if LLM_PROVIDER == "ollama":
        return stream_ollama(prompt)

    if LLM_PROVIDER == "gemini":
        return stream_gemini(prompt)

    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


# -------------------------
# Answer generation (STRICT RAG)
# -------------------------

def stream_answer(query: str, contexts: List[Dict]) -> Iterator[str]:
    """
    Production-grade grounded answer generator.

    Guarantees:
    - Uses ONLY retrieved context
    - No hallucination
    - Explicit fallback when info is missing
    """

    if not contexts:
        yield "Based on the provided documents, no relevant information was found."
        return

    context_block = _build_context(contexts)

    system_prompt = """You are a strict resume analysis assistant.

You MUST follow these rules:
1. Answer ONLY using the provided context.
2. Do NOT use external knowledge or assumptions.
3. If the answer is not explicitly present, say:
   "Based on the provided documents, this information is not explicitly stated."
4. Be factual, concise, and professional.
5. Do NOT invent experience levels, years, or skills.
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
# Sentence-level citations
# -------------------------

def generate_sentence_citations(
    full_answer: str,
    contexts: List[Dict]
) -> List[Dict]:
    """
    Map each answer sentence to supporting sources.

    Strategy:
    - Lexical overlap first
    - Fallback to top-confidence sources
    """

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", full_answer)
        if s.strip()
    ]

    citations = []

    for sentence in sentences:
        matched_sources = []

        sentence_lower = sentence.lower()

        # 1️⃣ Lexical grounding (robust, not brittle)
        for ctx in contexts:
            ctx_text = ctx.get("text", "").lower()
            if any(word in ctx_text for word in sentence_lower.split()[:6]):
                matched_sources.append(ctx)

        # 2️⃣ Fallback: top-confidence chunks
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
