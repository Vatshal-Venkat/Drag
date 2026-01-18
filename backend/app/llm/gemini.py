from typing import Iterator
import google.generativeai as genai

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_TEMPERATURE,
)


def stream_gemini(prompt: str) -> Iterator[str]:
    """
    Streams tokens from Gemini API.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config={
            "temperature": LLM_TEMPERATURE,
        },
    )

    response = model.generate_content(
        prompt,
        stream=True,
    )

    for chunk in response:
        if hasattr(chunk, "text") and chunk.text:
            yield chunk.text
