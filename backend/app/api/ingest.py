from fastapi import APIRouter, UploadFile, File, HTTPException
import logging

from app.services.file_loader import extract_text_from_file
from app.services.chunker import chunk_text
from app.services.embeddings import embed_texts
from app.vectorstore.store_manager import get_store_for_document
from app.registry.document_registry import register_document

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    try:
        # 1. Extract text
        documents = extract_text_from_file(file)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=400, detail=f"File extraction failed: {str(e)}")

    if not documents:
        raise HTTPException(status_code=400, detail="No text found in file")

    all_chunks = []
    all_metadata = []

    # 2. Page-aware chunking
    for doc in documents:
        text = doc.get("text", "")
        page = doc.get("page")
        source = file.filename

        if not text.strip():
            continue

        chunks = chunk_text(text)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({
                "source": source,
                "page": page,
                "text": chunk,
            })

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No chunks generated from document")

    # 3. Batch Embedding Generation 
    # (Handling API limits and model errors)
    try:
        # We process in batches inside embed_texts or here to avoid 413/429 errors
        embeddings = []
        batch_size = 100  # Conservative batch size for stability
        
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i : i + batch_size]
            batch_embeddings = embed_texts(batch)
            embeddings.extend(batch_embeddings)
            
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to generate embeddings. Check API key and model name."
        )

    # 4. Vector Store Management
    try:
        store = get_store_for_document(file.filename)
        store.add(
            embeddings=embeddings,
            metadatas=all_metadata,
        )
        store.save()
    except Exception as e:
        logger.error(f"Vector store error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save vectors to store.")

    # 5. Registry Update
    unique_pages = {m["page"] for m in all_metadata if m["page"] is not None}
    
    register_document(
        document_id=file.filename,
        pages=len(unique_pages),
        chunks=len(all_chunks),
    )

    return {
        "status": "ok",
        "document_id": file.filename,
        "pages": len(unique_pages),
        "chunks": len(all_chunks),
    }