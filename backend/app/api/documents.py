from fastapi import APIRouter
from app.registry.document_registry import list_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def get_documents():
    """
    Returns all uploaded documents (persistent registry).
    """
    return {
        "documents": list_documents()
    }
