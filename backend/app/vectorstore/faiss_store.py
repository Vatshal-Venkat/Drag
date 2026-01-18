import faiss
import numpy as np
import os
import pickle

class FAISSStore:
    def __init__(self, dim: int, path="data"):
        self.path = path
        self.index_path = f"{path}/index.faiss"
        self.meta_path = f"{path}/meta.pkl"

        os.makedirs(path, exist_ok=True)

        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = []

    def add(self, embeddings, metadatas):
        self.index.add(embeddings)
        self.metadata.extend(metadatas)
        self.save()

    def search(self, query_embedding, k=5):
        D, I = self.index.search(query_embedding, k)
        return [self.metadata[i] for i in I[0]]

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
