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


def _build_conversation(conversation_messages: Optional[List[Dict]]) -> str:
    if not conversation_messages:
        return ""

    formatted = []
    for msg in conversation_messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "").strip()
        if content:
            formatted.append(f"{role}: {content}")

    if not formatted:
        return ""

    return "\n".join(formatted)


def _build_observations(observations: Optional[List[Dict]]) -> str:
    if not observations:
        return ""

    obs_lines = [
        f"- {json.dumps(obs, ensure_ascii=False)}"
        for obs in observations
    ]

    return "Observations:\n" + "\n".join(obs_lines)


# =================================================
# AGENTIC SYSTEM PROMPT
# =================================================

BASE_SYSTEM_PROMPT = """You are an advanced conversational RAG generator.

Rules:
1. Use ONLY the provided document context for factual claims.
2. Conversation memory is for continuity — NOT for factual invention.
3. NEVER hallucinate missing document facts.
4. If context is insufficient, say so clearly.
5. Do NOT mention internal systems or architecture.
6. Respond clearly, concisely, and naturally.
"""


# =================================================
# LOW-LEVEL STREAMING LLM
# =================================================

def _stream_llm(
    user_prompt: str,
    *,
    system_prompt: Optional[str] = None,
) -> Iterator[str]:

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
# STREAMING ANSWER (UNIFIED CONVERSATIONAL PATH)
# =================================================

def stream_answer(
    query: str,
    contexts: List[Dict],
    *,
    summary: Optional[str] = None,
    conversation_messages: Optional[List[Dict]] = None,
    observations: Optional[List[Dict]] = None,
    use_human_feedback: bool = True,
) -> Iterator[str]:

    # Optional HITL injection
    if contexts and use_human_feedback and inject_human_feedback:
        contexts = inject_human_feedback(query, contexts)

    context_block = _build_context(contexts) if contexts else ""

    conversation_block = _build_conversation(conversation_messages)
    observation_block = _build_observations(observations)

    summary_block = ""
    if summary:
        summary_block = f"Conversation Summary:\n{summary.strip()}\n\n"

    # -------------------------------------------------
    # Prompt Construction
    # -------------------------------------------------

    user_prompt = f"""
{summary_block}
Recent Conversation:
{conversation_block}

Document Context:
{context_block}

{observation_block}

User Question:
{query}

Answer:
""".strip()

    buffer = ""
    sentence_end = re.compile(r"[.!?]\s*$")

    citation_map = {
        idx + 1: ctx for idx, ctx in enumerate(contexts)
    } if contexts else {}

    for token in _stream_llm(user_prompt):
        buffer += token
        yield token

        if contexts and sentence_end.search(buffer):
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
# COMPARISON GENERATION
# =================================================

def stream_aligned_comparison_answer(
    query: str,
    aligned_sections: List[Dict],
) -> Iterator[str]:

    if not aligned_sections:
        yield "No comparable sections were found across documents."
        return

    section_blocks = []

    for section in aligned_sections:
        doc_keys = [
            k for k in section.keys()
            if k not in ("section_id", "similarity")
        ]

        if len(doc_keys) < 2:
            continue

        doc_a, doc_b = doc_keys[0], doc_keys[1]

        block = f"""
Section {section['section_id']} (Similarity: {section['similarity']})

Document A:
{section[doc_a]['text']}

Document B:
{section[doc_b]['text']}
"""
        section_blocks.append(block.strip())

    combined_context = "\n\n---\n\n".join(section_blocks)

    system_prompt = BASE_SYSTEM_PROMPT + """

Task:
Perform a structured section-aligned comparison.

For each section:
- Explain similarities
- Explain differences
- Highlight conflicts if any

Be precise. Do not generalize beyond given text.
"""

    user_prompt = f"""
Aligned Sections:
{combined_context}

Comparison Question:
{query}

Answer:
""".strip()

    for token in _stream_llm(user_prompt, system_prompt=system_prompt):
        yield token


# =================================================
# NON-STREAMING GENERATION
# =================================================

def generate_answer(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
) -> str:

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
# SENTENCE-LEVEL CITATIONS
# =================================================

def generate_sentence_citations(
    full_answer: str,
    contexts: List[Dict]
) -> List[Dict]:

    if not contexts:
        return []

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