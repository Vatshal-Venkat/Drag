from fastapi import APIRouter
from app.schemas import QueryRequest, QueryResponse
from app.services.retriever import retrieve_context
from app.services.generator import generate_answer

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def query_rag(req: QueryRequest):
    contexts = retrieve_context(req.query, req.top_k)
    answer = generate_answer(req.query, contexts)
    return {
        "answer": answer,
        "sources": contexts
    }
