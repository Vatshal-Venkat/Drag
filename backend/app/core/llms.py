from typing import List, Dict, Iterator, Optional, Literal
import os

# --------------------------------------------------
# Local model imports (lazy-loaded)
# --------------------------------------------------

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# --------------------------------------------------
# External providers
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
    "tool",          # 🔹 NEW (Phase 4C)
]

# ==================================================
# MODEL CONFIGURATION
# ==================================================

DEFAULT_GROQ_MODEL = os.getenv(
    "GROQ_DEFAULT_MODEL",
    "llama-3.1-8b-instant",
)

DEFAULT_LOCAL_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==================================================
# LOCAL MODEL (LAZY LOAD)
# ==================================================

_local_tokenizer: Optional[AutoTokenizer] = None
_local_model: Optional[AutoModelForCausalLM] = None


def _load_local_model():
    """
    Lazy-load the local HuggingFace model.
    This ensures we do NOT load large models
    unless explicitly required.
    """
    global _local_model, _local_tokenizer

    if _local_model is not None and _local_tokenizer is not None:
        return

    _local_tokenizer = AutoTokenizer.from_pretrained(
        DEFAULT_LOCAL_MODEL
    )

    _local_model = AutoModelForCausalLM.from_pretrained(
        DEFAULT_LOCAL_MODEL,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto",
    )


# ==================================================
# PUBLIC LLM INTERFACE (AGENTIC, UNIFIED)
# ==================================================

def generate_text(
    *,
    messages: List[Dict[str, str]],
    role: LLMRole = "generator",
    stream: bool = False,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    provider: Literal["groq", "local"] = "groq",
) -> Iterator[str] | str:
    """
    Unified LLM entrypoint for ALL agents.

    Roles supported:
    - planner
    - generator
    - summarizer
    - chat
    - tool

    Providers:
    - groq (default)
    - local (offline / fallback)
    """

    # --------------------------------------------------
    # GROQ PROVIDER (DEFAULT)
    # --------------------------------------------------

    if provider == "groq":
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
        )

        # Explicit, readable return (no compression)
        return response.choices[0].message.content.strip()

    # --------------------------------------------------
    # LOCAL MODEL (FALLBACK / OFFLINE)
    # --------------------------------------------------

    _load_local_model()

    # Build a readable prompt (kept explicit)
    prompt_parts: List[str] = []

    for msg in messages:
        role_label = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        prompt_parts.append(f"{role_label}: {content}")

    prompt = "\n".join(prompt_parts)

    inputs = _local_tokenizer(
        prompt,
        return_tensors="pt",
    ).to(DEVICE)

    outputs = _local_model.generate(
        **inputs,
        max_new_tokens=max_tokens or 512,
        do_sample=False,
    )

    decoded = _local_tokenizer.decode(
        outputs[0],
        skip_special_tokens=True,
    )

    return decoded.strip()


# ==================================================
# ROLE-SPECIFIC HELPERS (KEPT EXPLICIT)
# ==================================================

def planner_llm(
    messages: List[Dict[str, str]],
    *,
    stream: bool = False,
):
    """
    LLM call dedicated for planning / ReAct.
    Temperature forced to 0.0 for determinism.
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
    LLM call dedicated for answer generation.
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
    LLM call dedicated for summarization / memory compression.
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
    LLM call dedicated for tool reasoning (if ever needed).
    Not used yet, but reserved for future extensions.
    """
    return generate_text(
        messages=messages,
        role="tool",
        stream=False,
        temperature=0.0,
    )
