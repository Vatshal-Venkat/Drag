from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import Any

from app.memory.summary_memory import (
    load_summary,
    update_summary,
)

from app.schemas.rag import QueryRequest
from app.services.retriever import (
    retrieve_context,
    retrieve_for_comparison,
)
from app.services.generator import (
    stream_answer,
    stream_comparison_answer,
    generate_sentence_citations,
)

router = APIRouter(prefix="/rag")


def make_json_safe(obj: Any):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj


@router.post("/query/stream")
def query_rag_stream(req: QueryRequest):

    # --------------------------------------------------
    # 🔹 VALIDATION
    # --------------------------------------------------

    if req.compare_mode:
        if not req.document_ids or len(req.document_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="compare_mode requires at least two document_ids"
            )
    else:
        if not req.document_id:
            raise HTTPException(
                status_code=400,
                detail="document_id is required for non-comparison queries"
            )

    # --------------------------------------------------
    # 🔹 COMPARISON MODE
    # --------------------------------------------------

    if req.compare_mode:
        grouped_contexts = retrieve_for_comparison(
            query=req.query,
            top_k=req.top_k,
            document_ids=req.document_ids,
        )

        def event_generator():
            # 1️⃣ Stream comparison answer
            for token in stream_comparison_answer(
                query=req.query,
                grouped_contexts=grouped_contexts,
            ):
                yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

            # 2️⃣ Send grouped sources
            yield f"data: {json.dumps({'type': 'sources', 'value': make_json_safe(grouped_contexts)})}\n\n"

            # 3️⃣ End
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )

    # --------------------------------------------------
    # 🔹 STANDARD SINGLE-DOCUMENT RAG
    # --------------------------------------------------

    contexts = retrieve_context(
        query=req.query,
        top_k=req.top_k,
        document_id=req.document_id,
    )

    def event_generator():
        full_answer = ""

        # 1️⃣ Stream tokens
        for token in stream_answer(
            query=req.query,
            contexts=contexts,
            use_human_feedback=req.use_human_feedback,
        ):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"

        
        previous_summary = load_summary()
        update_summary(
            previous_summary,
            req.query,
            full_answer,
        )

        # 2️⃣ Sentence-level citations
        citations = generate_sentence_citations(full_answer, contexts)
        yield f"data: {json.dumps({'type': 'citations', 'value': make_json_safe(citations)})}\n\n"

        # 3️⃣ Sources
        yield f"data: {json.dumps({'type': 'sources', 'value': make_json_safe(contexts)})}\n\n"

        # 4️⃣ End
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
