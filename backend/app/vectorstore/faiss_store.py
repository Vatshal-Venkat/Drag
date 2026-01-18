import faiss
import numpy as np
import os
import pickle
from typing import List, Dict




class FAISSStore:
    def __init__(self, dim: int, path: str = "data"):
        self.dim = dim
        self.path = path
        self.index_path = os.path.join(path, "index.faiss")
        self.meta_path = os.path.join(path, "meta.pkl")

        os.makedirs(path, exist_ok=True)

        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata: List[Dict] = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = []

    def add(self, embeddings: List[List[float]], metadatas: List[Dict]):
        if not embeddings:
            return

        vectors = np.array(embeddings).astype("float32")

        if vectors.shape[1] != self.dim:
            raise ValueError("Embedding dimension mismatch")

        start_id = len(self.metadata)

        for i, meta in enumerate(metadatas):
            meta["id"] = start_id + i

        self.index.add(vectors)
        self.metadata.extend(metadatas)

        self.save()

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        if self.index.ntotal == 0:
            return []

        query_vector = (
            np.array(query_embedding)
            .astype("float32")
            .reshape(1, -1)
        )

        distances, indices = self.index.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                item = dict(self.metadata[idx])
                item["distance"] = float(dist)
                item["confidence"] = round(1 / (1 + dist), 4)
                results.append(item)

        return results

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)


# ---------- GLOBAL STORE SINGLETON ----------

_store = None


def get_store():
    """
    Returns a singleton FAISSStore instance.
    """
    global _store

    if _store is None:
        _store = FAISSStore(dim=384)

    return _store
