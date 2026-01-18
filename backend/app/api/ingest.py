from fastapi import APIRouter, UploadFile
import pdfplumber

from app.services.chunker import chunk_text
from backend.app.services.embeddings import embed_texts
from app.vectorstore.faiss_store import FAISSStore


router = APIRouter()
store = FAISSStore(dim=384)

@router.post("/ingest")
async def ingest(file: UploadFile):
    text = ""
    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    chunks = chunk_text(text)
    embeddings = embed_texts(chunks)

    metadata = [{"text": c, "source": file.filename} for c in chunks]
    store.add(embeddings, metadata)

    return {"status": "ingested", "chunks": len(chunks)}
