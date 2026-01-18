from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.schemas import QueryRequest
from app.services.retriever import retrieve_context
from app.services.generator import (
    stream_answer,
    generate_sentence_citations,
)

router = APIRouter()


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

        yield f"data: {json.dumps({'type': 'citations', 'value': citations})}\n\n"

        # 3️⃣ Sources (deduplicated)
        sources = {
            c["id"]: {
                "id": c["id"],
                "source": c["source"],
                "page": c.get("page"),
                "confidence": c["confidence"],
                "text": c["text"],
            }
            for c in contexts
        }

        yield f"data: {json.dumps({'type': 'sources', 'value': list(sources.values())})}\n\n"

        # 4️⃣ End
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
