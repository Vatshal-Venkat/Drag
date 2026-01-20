from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from typing import Any

from app.schemas.rag import QueryRequest
from app.services.retriever import retrieve_context
from app.services.generator import (
    stream_answer,
    generate_sentence_citations,
)

router = APIRouter()


def make_json_safe(obj: Any):
    """
    Recursively convert numpy / non-JSON-safe objects
    (e.g., float32, int64) into native Python types.
    """
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if hasattr(obj, "item"):  # numpy scalar (float32, int64, etc.)
        return obj.item()
    return obj


@router.post("/query/stream")
def query_rag_stream(req: QueryRequest):
    contexts = retrieve_context(req.query, req.top_k)

    def event_generator():
        full_answer = ""

        # 1️⃣ Stream tokens
        for token in stream_answer(req.query, contexts):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

        # 2️⃣ Sentence-level citations
        citations = generate_sentence_citations(
            full_answer,
            contexts,
        )

        yield f"data: {json.dumps({'type': 'citations', 'value': make_json_safe(citations)})}\n\n"

        # 3️⃣ Sources (deduplicated + JSON-safe)
        sources = {
            c["id"]: {
                "id": c["id"],
                "source": c.get("source"),
                "page": c.get("page"),
                "confidence": c.get("confidence"),
                "text": c.get("text"),
            }
            for c in contexts
        }

        safe_sources = make_json_safe(list(sources.values()))

        yield f"data: {json.dumps({'type': 'sources', 'value': safe_sources})}\n\n"

        # 4️⃣ End
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
