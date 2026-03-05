import os
import tempfile
from typing import List, Dict
from pypdf import PdfReader
from docx import Document
from pptx import Presentation
import openpyxl
from fastapi import UploadFile
from google import genai
from google.genai import types

def _get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)


def extract_media_with_gemini(file_path: str, mime_type: str, filename: str) -> List[Dict]:
    """
    Uses Gemini 2.5 Flash to extract a comprehensive text description/transcript 
    from images, audio, or video files.
    """
    client = _get_genai_client()
    
    # Upload file to Gemini File API
    # We use a context manager if possible, but genai.Client.files.upload returns a file object
    uploaded_file = client.files.upload(file=file_path, config={'mime_type': mime_type})
    
    prompt = (
        "You are an expert data extractor for a Retrieval-Augmented Generation (RAG) system. "
        "Analyze this file comprehensively. "
        "If it's an image, describe all visual elements, text (OCR), charts, and context in extreme detail. "
        "If it's audio/video, provide a full accurate transcript and describe any important visual/auditory context. "
        "Return ONLY the extracted text and detailed descriptions. Do not add conversational filler."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        text = response.text.strip()
    finally:
        # Always clean up the file from Gemini's storage
        client.files.delete(name=uploaded_file.name)
        
    if not text:
        return []
        
    return [{
        "text": text,
        "page": 1, 
        "source": filename
    }]


async def extract_text_from_file(file: UploadFile) -> List[Dict]:
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
    
    # Read the file content into memory since we might need it as a file path for Gemini
    content = await file.read()

    # -------- PDF --------
    if lower.endswith(".pdf"):
        from io import BytesIO
        reader = PdfReader(BytesIO(content))

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
        from io import BytesIO
        doc = Document(BytesIO(content))
        full_text = "\n".join(p.text for p in doc.paragraphs).strip()

        if not full_text:
            return []

        documents.append({
            "text": full_text,
            "page": None,
            "source": filename,
        })

        return documents
        
    # -------- PPTX --------
    if lower.endswith(".pptx"):
        from io import BytesIO
        prs = Presentation(BytesIO(content))
        for i, slide in enumerate(prs.slides):
            text_runs = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text_runs.append(shape.text)
            slide_text = "\n".join(text_runs).strip()
            if slide_text:
                documents.append({
                    "text": slide_text,
                    "page": i + 1, # Treat slides as pages
                    "source": filename
                })
        return documents
        
    # -------- XLSX --------
    if lower.endswith(".xlsx"):
        from io import BytesIO
        wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
        for i, sheet_name in enumerate(wb.sheetnames):
            sheet = wb[sheet_name]
            sheet_text = []
            sheet_text.append(f"Sheet Name: {sheet_name}")
            for row in sheet.iter_rows(values_only=True):
                row_values = [str(cell) if cell is not None else "" for cell in row]
                # Only add rows that have at least some data
                if any(row_values):
                    sheet_text.append(" | ".join(row_values))
            
            full_sheet_text = "\n".join(sheet_text).strip()
            if len(full_sheet_text) > len(f"Sheet Name: {sheet_name}"):
                documents.append({
                    "text": full_sheet_text,
                    "page": i + 1, # Treat sheets as pages
                    "source": filename
                })
        return documents
        
    # -------- MULTIMEDIA (Images, Audio, Video) --------
    mime_type = file.content_type
    if mime_type and (mime_type.startswith("image/") or mime_type.startswith("audio/") or mime_type.startswith("video/")):
        # Write to a temporary file because Gemini File API requires a file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
            
        try:
            documents = extract_media_with_gemini(temp_path, mime_type, filename)
            return documents
        finally:
            os.remove(temp_path)

    # -------- UNSUPPORTED --------
    raise ValueError(f"Unsupported file type: {filename} with mime {mime_type}")
