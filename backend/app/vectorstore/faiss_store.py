import faiss
import numpy as np
import os
import pickle
from typing import List, Dict


class FAISSStore:
    """
    A document-scoped FAISS vector store.
    Each instance represents ONE document.
    """

    def __init__(self, dim: int, store_dir: str):
        self.dim = dim
        self.store_dir = store_dir

        os.makedirs(store_dir, exist_ok=True)

        self.index_path = os.path.join(store_dir, "index.faiss")
        self.meta_path = os.path.join(store_dir, "meta.pkl")

        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            # Load existing index
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata: List[Dict] = pickle.load(f)
        else:
            # Create new index
            self.index = faiss.IndexFlatL2(dim)
            self.metadata: List[Dict] = []

    # -------------------------
    # Add embeddings
    # -------------------------

    def add(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict],
    ):
        if not embeddings:
            return

        if len(embeddings) != len(metadatas):
            raise ValueError("Embeddings and metadatas length mismatch")

        vectors = np.array(embeddings, dtype="float32")

        if vectors.shape[1] != self.dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dim}, got {vectors.shape[1]}"
            )

        start_id = len(self.metadata)

        for i, meta in enumerate(metadatas):
            # Stable per-document chunk ID
            meta["id"] = start_id + i

        self.index.add(vectors)
        self.metadata.extend(metadatas)

    # -------------------------
    # Search
    # -------------------------

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        if self.index.ntotal == 0:
            return []

        query_vector = (
            np.array(query_embedding, dtype="float32")
            .reshape(1, -1)
        )

        distances, indices = self.index.search(query_vector, k)

        results: List[Dict] = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue

            item = dict(self.metadata[idx])
            item["distance"] = float(dist)
            item["confidence"] = round(1 / (1 + dist), 4)
            results.append(item)

        return results

    # -------------------------
    # 🔹 NEW: BM25 SUPPORT (ADDITIVE ONLY)
    # -------------------------

    def get_all_texts(self) -> List[str]:
        """
        Return all chunk texts in this store (for BM25).
        """
        return [m.get("text", "") for m in self.metadata]

    def get_all_metadata(self) -> List[Dict]:
        """
        Return full metadata list (safe copy).
        """
        return list(self.metadata)

    # -------------------------
    # Persistence
    # -------------------------

    def save(self):
        """
        Persist index and metadata to disk.
        """
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
