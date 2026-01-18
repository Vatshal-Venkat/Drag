from typing import List, Dict
from pypdf import PdfReader
from docx import Document
from fastapi import UploadFile


def extract_text_from_file(file: UploadFile) -> List[Dict]:
    """
    Extract text from file WITH metadata.

    Returns a list of:
    {
        "text": str,
        "page": int | None,
        "source": filename
    }
    """

    filename = file.filename
    lower = filename.lower()

    documents: List[Dict] = []

    # -------- PDF --------
    if lower.endswith(".pdf"):
        reader = PdfReader(file.file)

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()

            if not text:
                continue

            documents.append({
                "text": text,
                "page": page_idx + 1,  # human-readable page number
                "source": filename,
            })

        return documents

    # -------- DOCX --------
    if lower.endswith(".docx") or lower.endswith(".doc"):
        doc = Document(file.file)
        full_text = "\n".join(p.text for p in doc.paragraphs).strip()

        if not full_text:
            return []

        documents.append({
            "text": full_text,
            "page": None,
            "source": filename,
        })

        return documents

    # -------- UNSUPPORTED --------
    raise ValueError("Unsupported file type")
