from typing import List, Dict, Iterator, Optional, Literal
import os

# --------------------------------------------------
# External provider (GROQ ONLY)
# --------------------------------------------------

from app.llm.groq import groq_chat, groq_stream

# ==================================================
# LLM ROLE DEFINITIONS
# ==================================================

LLMRole = Literal[
    "planner",
    "generator",
    "summarizer",
    "chat",
    "tool",
]

# ==================================================
# MODEL CONFIGURATION
# ==================================================

DEFAULT_GROQ_MODEL = os.getenv(
    "GROQ_DEFAULT_MODEL",
    "llama-3.1-8b-instant",
)

# ==================================================
# PUBLIC LLM INTERFACE
# ==================================================

def generate_text(
    *,
    messages: List[Dict[str, str]],
    role: LLMRole = "generator",
    stream: bool = False,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    provider: Literal["groq"] = "groq",
) -> Iterator[str] | str:
    """
    Unified LLM entrypoint.

    Provider:
    - groq (only supported provider in this deployment)
    """

    if provider != "groq":
        raise RuntimeError(
            "Only GROQ provider is supported in this deployment."
        )

    if stream:
        return groq_stream(
            messages=messages,
            model=DEFAULT_GROQ_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    response = groq_chat(
        messages=messages,
        model=DEFAULT_GROQ_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()


# ==================================================
# ROLE-SPECIFIC HELPERS
# ==================================================

def planner_llm(
    messages: List[Dict[str, str]],
    *,
    stream: bool = False,
):
    """
    Planning / reasoning LLM.
    Deterministic (temperature = 0).
    """
    return generate_text(
        messages=messages,
        role="planner",
        stream=stream,
        temperature=0.0,
    )


def generator_llm(
    messages: List[Dict[str, str]],
    *,
    stream: bool = True,
):
    """
    Main answer generation LLM.
    """
    return generate_text(
        messages=messages,
        role="generator",
        stream=stream,
        temperature=0.2,
    )


def summarizer_llm(
    messages: List[Dict[str, str]],
):
    """
    Summarization / memory compression LLM.
    """
    return generate_text(
        messages=messages,
        role="summarizer",
        stream=False,
        temperature=0.1,
    )


def tool_llm(
    messages: List[Dict[str, str]],
):
    """
    Tool reasoning LLM (reserved for future use).
    """
    return generate_text(
        messages=messages,
        role="tool",
        stream=False,
        temperature=0.0,
    )
