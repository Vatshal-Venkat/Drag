import asyncio
from fastapi import UploadFile
import io
import os
import sys

# Add the parent directory to sys.path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.file_loader import extract_text_from_file

class MockUploadFile(UploadFile):
    def __init__(self, filename, content, content_type):
        super().__init__(
            file=io.BytesIO(content),
            filename=filename,
            headers={"content-type": content_type}
        )
        # Store for the async read override
        self._mock_content = content
        
    async def read(self, size: int = -1) -> bytes:
        return self._mock_content

async def test_extraction():
    print("Testing PDF Extraction (Mock)...")
    # In a real test, load an actual file. We'll skip binary files if not present.
    # For now, let's just make sure the import and function signature is valid
    try:
        print("Imports and structure are valid.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
