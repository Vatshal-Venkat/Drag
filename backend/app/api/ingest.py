from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.file_loader import extract_text_from_file
from app.services.chunker import chunk_text
from app.services.embeddings import embed_texts
from app.vectorstore.faiss_store import get_store

router = APIRouter()


@router.post("/ingest/file")
def ingest_file(file: UploadFile = File(...)):
    try:
        documents = extract_text_from_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not documents:
        raise HTTPException(status_code=400, detail="No text found in file")

    all_chunks = []
    all_metadata = []

    # -------- PAGE-AWARE CHUNKING --------
    for doc in documents:
        text = doc["text"]
        page = doc["page"]
        source = doc["source"]

        chunks = chunk_text(text)

        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadata.append({
                "source": source,
                "page": page,
                "text": chunk,  # store text explicitly for citations
            })

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No chunks generated")

    # -------- EMBEDDINGS --------
    embeddings = embed_texts(all_chunks)

    # -------- STORE --------
    store = get_store()
    store.add(
        embeddings=embeddings,
        metadatas=all_metadata,
    )

    return {
        "status": "ok",
        "filename": file.filename,
        "pages": len(set(m["page"] for m in all_metadata if m["page"])),
        "chunks": len(all_chunks),
    }
