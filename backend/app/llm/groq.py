from groq import Groq
from typing import List, Dict, Generator, Optional
import os
import time

# -------------------------
# Existing client (UNCHANGED)
# -------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# -------------------------
# EXISTING FUNCTION (UNCHANGED)
# -------------------------
def groq_chat(
    messages: List[Dict[str, str]],
    model: str = "llama-3.1-8b-instant",
):
    """
    Non-streaming Groq chat completion.
    Kept for backward compatibility.
    """
    return client.chat.completions.create(
        model=model,
        messages=messages,
    )


# =====================================================
# 🔹 EXTENSIONS BELOW (ADDITIVE ONLY)
# =====================================================

def groq_chat_with_config(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    timeout: int = 60,
):
    """
    Non-streaming Groq chat with full configuration.
    """
    start = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    elapsed = round(time.time() - start, 3)

    return {
        "response": response,
        "latency": elapsed,
        "model": model,
    }


def groq_stream(
    messages: List[Dict[str, str]],
    model: str = "llama-3.1-8b-instant",
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
) -> Generator[str, None, None]:
    """
    Streaming Groq completion.
    Yields tokens as they arrive.
    """

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        if not chunk:
            continue

        delta = chunk.choices[0].delta

        if delta and delta.content:
            yield delta.content


def groq_healthcheck() -> Dict[str, str]:
    """
    Lightweight health check to verify Groq connectivity.
    """
    try:
        test = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "ping"}
            ],
            max_tokens=1,
        )

        return {
            "status": "ok",
            "model": test.model,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
