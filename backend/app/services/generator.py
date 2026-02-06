from typing import List, Dict, Iterator, Optional
import re
import textwrap
import json

from app.llm.groq import groq_stream, groq_chat
from app.config import GROQ_MODEL, LLM_TEMPERATURE

# NOTE: HITL injection is optional and non-breaking
try:
    from app.services.hitl import inject_human_feedback
except Exception:
    inject_human_feedback = None


# =================================================
# AGENT METADATA
# =================================================

AGENT_NAME = "generator_agent"
AGENT_DESCRIPTION = (
    "Synthesizes a final answer strictly from provided observations "
    "and retrieved context. Does not retrieve or plan."
)


# =================================================
# CONTEXT FORMATTING
# =================================================

def _build_context(contexts: List[Dict]) -> str:
    """
    Convert retrieved contexts into a structured,
    LLM-safe block for generation.
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


def _build_comparison_context(
    grouped_contexts: Dict[str, List[Dict]]
) -> str:
    """
    Build structured context grouped per document.
    Used by comparison / multi-doc agent plans.
    """

    sections = []

    for doc_id, contexts in grouped_contexts.items():
        header = f"\n=== Document: {doc_id} ===\n"
        body = _build_context(contexts) if contexts else "No relevant content found."
        sections.append(header + body)

    return "\n\n".join(sections)


# =================================================
# AGENTIC SYSTEM PROMPT
# =================================================

BASE_SYSTEM_PROMPT = """You are an Agentic RAG Generator Agent.

Rules:
1. Use ONLY the provided context and observations
2. NEVER hallucinate or assume missing facts
3. If the context is insufficient, say so explicitly
4. Do NOT mention agents, tools, or internal systems
5. Respond clearly, concisely, and factually
"""


# =================================================
# LOW-LEVEL STREAMING LLM
# =================================================

def _stream_llm(
    user_prompt: str,
    *,
    system_prompt: Optional[str] = None,
) -> Iterator[str]:
    """
    Internal streaming LLM call.
    This is the ONLY place where the LLM is touched.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt or BASE_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    for token in groq_stream(
        messages=messages,
        model=GROQ_MODEL,
        temperature=LLM_TEMPERATURE,
    ):
        yield token


# =================================================
# AGENTIC STREAMING ANSWER (MAIN PATH)
# =================================================

def stream_answer(
    query: str,
    contexts: List[Dict],
    *,
    use_human_feedback: bool = True,
    observations: Optional[List[Dict]] = None,
) -> Iterator[str]:
    """
    AGENT TOOL: generator_agent

    This function assumes:
    - Retrieval, reranking, planning already happened
    - Contexts are FINAL inputs
    """

    if not contexts:
        yield "Based on the provided documents, no relevant information was found."
        return

    # Optional HITL injection (safe, additive)
    if use_human_feedback and inject_human_feedback:
        contexts = inject_human_feedback(query, contexts)

    # -------------------------------------------------
    # Context + Observations
    # -------------------------------------------------

    context_block = _build_context(contexts)

    observation_block = ""
    if observations:
        observation_block = "\n\n".join(
            f"- {json.dumps(obs, ensure_ascii=False)}"
            for obs in observations
        )
        observation_block = f"\n\nObservations:\n{observation_block}"

    # -------------------------------------------------
    # Prompt
    # -------------------------------------------------

    user_prompt = f"""
Context:
{context_block}
{observation_block}

Question:
{query}

Answer:
""".strip()

    buffer = ""
    sentence_end = re.compile(r"[.!?]\s*$")

    citation_map = {
        idx + 1: ctx for idx, ctx in enumerate(contexts)
    }

    # -------------------------------------------------
    # Stream tokens with inline citations
    # -------------------------------------------------

    for token in _stream_llm(user_prompt):
        buffer += token
        yield token

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


# =================================================
# COMPARISON GENERATION (AGENTIC)
# =================================================

def stream_comparison_answer(
    query: str,
    grouped_contexts: Dict[str, List[Dict]],
) -> Iterator[str]:
    """
    AGENT TOOL: generator_agent (comparison mode)
    """

    context_block = _build_comparison_context(grouped_contexts)

    system_prompt = BASE_SYSTEM_PROMPT + """

Task:
Compare multiple documents using ONLY the provided context.

Output Structure:
- Similarities
- Differences
- Conflicts (if any)
"""

    user_prompt = f"""
Documents Context:
{context_block}

Comparison Question:
{query}

Answer:
""".strip()

    for token in _stream_llm(user_prompt, system_prompt=system_prompt):
        yield token


# =================================================
# NON-STREAMING GENERATION (AGENTIC)
# =================================================

def generate_answer(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Non-streaming generation for summaries or background tasks.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt or BASE_SYSTEM_PROMPT,
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


# =================================================
# SENTENCE-LEVEL CITATIONS (POST-PROCESSING)
# =================================================

def generate_sentence_citations(
    full_answer: str,
    contexts: List[Dict]
) -> List[Dict]:
    """
    Optional post-processing step for UI citation rendering.
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
