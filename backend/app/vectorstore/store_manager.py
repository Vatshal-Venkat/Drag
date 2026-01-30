import os
from typing import Optional, List, Dict

from rank_bm25 import BM25Okapi
from app.vectorstore.faiss_store import FAISSStore

BASE_STORE_DIR = "backend/vectorstores"
EMBED_DIM = 384
DEFAULT_STORE_ID = "__default__"

# ---------------------------
# 🔹 BM25 CACHE (NEW)
# ---------------------------

_BM25_CACHE: Dict[str, Dict] = {}


def get_bm25_for_store(store: FAISSStore):
    """
    Returns cached BM25 index for a store.
    Rebuilds only if metadata size changes.
    """
    store_id = store.store_dir
    texts = store.get_all_texts()
    size = len(texts)

    cached = _BM25_CACHE.get(store_id)

    if cached and cached["size"] == size:
        return cached["bm25"]

    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)

    _BM25_CACHE[store_id] = {
        "bm25": bm25,
        "size": size,
    }

    return bm25


# ---------------------------
# EXISTING CODE (UNCHANGED)
# ---------------------------

def _sanitize_id(raw_id: str) -> str:
    return raw_id.replace(".pdf", "").replace(" ", "_").lower()


def _get_store_dir(store_id: str) -> str:
    return os.path.join(BASE_STORE_DIR, store_id)


def get_store_for_document(doc_id: str) -> FAISSStore:
    safe_id = _sanitize_id(doc_id)
    store_dir = _get_store_dir(safe_id)
    return FAISSStore(dim=EMBED_DIM, store_dir=store_dir)


def get_default_store() -> Optional[FAISSStore]:
    store_dir = _get_store_dir(DEFAULT_STORE_ID)
    if not os.path.exists(store_dir):
        return None
    return FAISSStore(dim=EMBED_DIM, store_dir=store_dir)


def set_default_store_from_document(doc_id: str) -> FAISSStore:
    source_store = get_store_for_document(doc_id)
    default_store_dir = _get_store_dir(DEFAULT_STORE_ID)
    os.makedirs(default_store_dir, exist_ok=True)
    source_store.save()
    return FAISSStore(dim=EMBED_DIM, store_dir=default_store_dir)


def list_all_document_stores() -> List[FAISSStore]:
    stores: List[FAISSStore] = []

    if not os.path.exists(BASE_STORE_DIR):
        return stores

    for name in os.listdir(BASE_STORE_DIR):
        store_dir = _get_store_dir(name)
        if not os.path.isdir(store_dir):
            continue

        if os.path.exists(os.path.join(store_dir, "index.faiss")):
            stores.append(FAISSStore(dim=EMBED_DIM, store_dir=store_dir))

    return stores
