"""
Run this locally to ingest documents and build FAISS indexes.
DO NOT run on Render.
"""

import os
from app.services.file_loader import extract_text_from_file
from app.services.chunker import chunk_text
from app.services.embeddings import embed_texts
from app.vectorstore.store_manager import get_store_for_document

DATA_DIR = "data/documents"

def ingest_all():
    for filename in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, filename)

        print(f"Ingesting {filename}...")

        text = extract_text_from_file(path)
        chunks = chunk_text(text)
        embeddings = embed_texts(chunks)

        store = get_store_for_document(filename)
        store.add(chunks, embeddings)
        store.save()

        print(f"Saved FAISS index for {filename}")

if __name__ == "__main__":
    ingest_all()
