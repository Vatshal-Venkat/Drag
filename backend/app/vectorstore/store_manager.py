import os
from typing import Optional

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

    Useful when:
    - Only one document exists
    - First ingestion should power chat
    """
    source_store = get_store_for_document(doc_id)
    default_store_dir = _get_store_dir(DEFAULT_STORE_ID)

    # Ensure directory exists
    os.makedirs(default_store_dir, exist_ok=True)

    # Persist source store into default location
    source_store.save(default_store_dir)

    return FAISSStore(
        dim=EMBED_DIM,
        store_dir=default_store_dir,
    )