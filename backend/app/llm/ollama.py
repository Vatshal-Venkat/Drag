import requests
from typing import Iterator

from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    LLM_TEMPERATURE,
)


def stream_ollama(prompt: str) -> Iterator[str]:
    """
    Streams tokens from Ollama using its HTTP API.
    """

    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": LLM_TEMPERATURE,
        },
    }

    with requests.post(url, json=payload, stream=True, timeout=120) as r:
        r.raise_for_status()

        for line in r.iter_lines():
            if not line:
                continue

            data = line.decode("utf-8")

            if '"done":true' in data:
                break

            try:
                token = eval(data).get("response", "")
                if token:
                    yield token
            except Exception:
                continue
