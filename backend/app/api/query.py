from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.schemas import QueryRequest
from app.services.retriever import retrieve_context
from app.services.generator import stream_answer, generate_citations

router = APIRouter()


@router.post("/query/stream")
def query_rag_stream(req: QueryRequest):
    contexts = retrieve_context(req.query, req.top_k)

    def event_generator():
        # 1️⃣ Stream tokens
        for token in stream_answer(req.query, contexts):
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

        # 2️⃣ Send citations
        citations = generate_citations(req.query, contexts)
        yield f"data: {json.dumps({'type': 'citations', 'value': citations})}\n\n"

        # 3️⃣ Send sources
        yield f"data: {json.dumps({'type': 'sources', 'value': contexts})}\n\n"

        # 4️⃣ End
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )