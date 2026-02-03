import os
import json
from typing import Dict, List

REGISTRY_DIR = "backend/registry"
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "documents.json")

os.makedirs(REGISTRY_DIR, exist_ok=True)


def _load_registry() -> Dict[str, Dict]:
    if not os.path.exists(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(registry: Dict[str, Dict]):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def register_document(
    document_id: str,
    pages: int,
    chunks: int,
):
    registry = _load_registry()

    if document_id not in registry:
        registry[document_id] = {
            "document_id": document_id,
            "pages": pages,
            "chunks": chunks,
        }

    _save_registry(registry)


def list_documents() -> List[Dict]:
    registry = _load_registry()
    return list(registry.values())
