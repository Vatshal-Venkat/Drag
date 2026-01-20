import os
from app.vectorstore.faiss_store import FAISSStore

BASE_STORE_DIR = "backend/vectorstores"
EMBED_DIM = 384


def get_store_for_document(doc_id: str) -> FAISSStore:
    safe_id = (
        doc_id
        .replace(".pdf", "")
        .replace(" ", "_")
        .lower()
    )

    store_dir = os.path.join(BASE_STORE_DIR, safe_id)
    return FAISSStore(dim=EMBED_DIM, store_dir=store_dir)
