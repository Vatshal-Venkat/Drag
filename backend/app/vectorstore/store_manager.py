import os
from typing import Optional, List, Dict

from rank_bm25 import BM25Okapi
from app.vectorstore.faiss_store import FAISSStore
from app.core.config import VECTORSTORE_BASE_DIR, EMBED_DIM

# ---------------------------
# Config (Linked to app/core/config.py)
# ---------------------------

BASE_STORE_DIR = VECTORSTORE_BASE_DIR
# EMBED_DIM is imported directly from config (768)
DEFAULT_STORE_ID = "__default__"

# ---------------------------
# 🔹 BM25 CACHE
# ---------------------------

_BM25_CACHE: Dict[str, Dict] = {}


def get_bm25_for_store(store: FAISSStore) -> BM25Okapi:
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

    # Use a slightly more robust tokenizer
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)

    _BM25_CACHE[store_id] = {
        "bm25": bm25,
        "size": size,
    }

    return bm25


# ---------------------------
# Store helpers
# ---------------------------

def _sanitize_id(raw_id: str) -> str:
    """Removes extensions and replaces spaces for safe directory naming."""
    name_without_ext = os.path.splitext(raw_id)[0]
    return name_without_ext.replace(" ", "_").replace(".", "_").lower()


def _get_store_dir(store_id: str) -> str:
    return os.path.join(BASE_STORE_DIR, store_id)


def get_store_for_document(doc_id: str) -> FAISSStore:
    """
    Returns a FAISS store for a specific document.
    Does NOT load anything eagerly.
    """
    safe_id = _sanitize_id(doc_id)
    store_dir = _get_store_dir(safe_id)
    return FAISSStore(dim=EMBED_DIM, store_dir=store_dir)


def get_default_store() -> Optional[FAISSStore]:
    """
    Returns the default FAISS store if it exists.
    """
    store_dir = _get_store_dir(DEFAULT_STORE_ID)
    if not os.path.exists(store_dir):
        return None

    return FAISSStore(dim=EMBED_DIM, store_dir=store_dir)


def set_default_store_from_document(doc_id: str) -> FAISSStore:
    """
    Copies a document store as the default store.
    """
    source_store = get_store_for_document(doc_id)
    default_store_dir = _get_store_dir(DEFAULT_STORE_ID)

    os.makedirs(default_store_dir, exist_ok=True)
    # Ensure source is saved before identifying it as default
    source_store.save()

    return FAISSStore(dim=EMBED_DIM, store_dir=default_store_dir)


def list_all_document_stores() -> List[FAISSStore]:
    """
    Lists all document FAISS stores on disk.
    """
    stores: List[FAISSStore] = []

    if not os.path.exists(BASE_STORE_DIR):
        return stores

    for name in os.listdir(BASE_STORE_DIR):
        store_dir = _get_store_dir(name)
        if not os.path.isdir(store_dir) or name == DEFAULT_STORE_ID:
            continue

        # Check for both index and metadata to ensure it's a valid store
        if os.path.exists(os.path.join(store_dir, "index.faiss")):
            stores.append(
                FAISSStore(dim=EMBED_DIM, store_dir=store_dir)
            )

    return stores