import os
import json
import hashlib
from typing import Dict, Optional, List
from datetime import datetime

# ==================================================
# GLOBAL DOCUMENT MEMORY (PERSISTENT)
# ==================================================

MEMORY_DIR = "backend/memory"
DOCUMENT_REGISTRY_FILE = os.path.join(MEMORY_DIR, "documents.json")

os.makedirs(MEMORY_DIR, exist_ok=True)


def _load_registry() -> Dict[str, Dict]:
    if not os.path.exists(DOCUMENT_REGISTRY_FILE):
        return {}
    with open(DOCUMENT_REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(registry: Dict[str, Dict]):
    with open(DOCUMENT_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def _hash_file(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


# --------------------------------------------------
# PUBLIC API
# --------------------------------------------------

def register_document(
    *,
    filename: str,
    file_bytes: bytes,
    document_id: str,
    vectorstore_path: str,
) -> Dict:
    registry = _load_registry()
    file_hash = _hash_file(file_bytes)

    if file_hash in registry:
        return registry[file_hash]

    entry = {
        "document_id": document_id,
        "filename": filename,
        "file_hash": file_hash,
        "vectorstore_path": vectorstore_path,
        "created_at": datetime.utcnow().isoformat(),
        "persistent": True,
    }

    registry[file_hash] = entry
    _save_registry(registry)

    return entry


def get_document_by_hash(file_hash: str) -> Optional[Dict]:
    return _load_registry().get(file_hash)


def get_document_by_id(document_id: str) -> Optional[Dict]:
    for doc in _load_registry().values():
        if doc.get("document_id") == document_id:
            return doc
    return None


def list_documents() -> List[Dict]:
    return list(_load_registry().values())


def delete_document(document_id: str) -> bool:
    registry = _load_registry()
    for key, doc in list(registry.items()):
        if doc.get("document_id") == document_id:
            del registry[key]
            _save_registry(registry)
            return True
    return False
