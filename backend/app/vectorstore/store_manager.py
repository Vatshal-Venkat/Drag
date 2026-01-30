import os
from typing import Optional, List

from app.vectorstore.faiss_store import FAISSStore

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_STORE_DIR = "backend/vectorstores"
EMBED_DIM = 384

# Global default store directory (for chat)
DEFAULT_STORE_ID = "__default__"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _sanitize_id(raw_id: str) -> str:
    return (
        raw_id
        .replace(".pdf", "")
        .replace(" ", "_")
        .lower()
    )


def _get_store_dir(store_id: str) -> str:
    return os.path.join(BASE_STORE_DIR, store_id)


# --------------------------------------------------
# Public API (EXISTING + EXTENDED)
# --------------------------------------------------

def get_store_for_document(doc_id: str) -> FAISSStore:
    """
    Get (or create) a FAISS store for a specific document.

    Existing behavior — DO NOT BREAK.
    """
    safe_id = _sanitize_id(doc_id)
    store_dir = _get_store_dir(safe_id)

    return FAISSStore(
        dim=EMBED_DIM,
        store_dir=store_dir,
    )


def get_default_store() -> Optional[FAISSStore]:
    """
    Get the default/global FAISS store used for chat.

    Returns None if it does not exist yet.
    """
    store_dir = _get_store_dir(DEFAULT_STORE_ID)

    if not os.path.exists(store_dir):
        return None

    return FAISSStore(
        dim=EMBED_DIM,
        store_dir=store_dir,
    )


def set_default_store_from_document(doc_id: str) -> FAISSStore:
    """
    Promote a document store to become the default/global store.
    """
    source_store = get_store_for_document(doc_id)
    default_store_dir = _get_store_dir(DEFAULT_STORE_ID)

    os.makedirs(default_store_dir, exist_ok=True)

    source_store.save()

    return FAISSStore(
        dim=EMBED_DIM,
        store_dir=default_store_dir,
    )


# --------------------------------------------------
# 🔹 NEW: MULTI-DOCUMENT DISCOVERY (ADDITIVE)
# --------------------------------------------------

def list_all_document_stores() -> List[FAISSStore]:
    """
    Return FAISSStore objects for all document folders.
    """
    stores: List[FAISSStore] = []

    if not os.path.exists(BASE_STORE_DIR):
        return stores

    for name in os.listdir(BASE_STORE_DIR):
        store_dir = _get_store_dir(name)
        if not os.path.isdir(store_dir):
            continue

        index_path = os.path.join(store_dir, "index.faiss")
        meta_path = os.path.join(store_dir, "meta.pkl")

        if os.path.exists(index_path) and os.path.exists(meta_path):
            stores.append(
                FAISSStore(dim=EMBED_DIM, store_dir=store_dir)
            )

    return stores
