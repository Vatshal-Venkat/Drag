import asyncio
import os
from fastapi import UploadFile
from app.services.file_loader import extract_text_from_file

async def run_test():
    class MockUploadFile:
        def __init__(self, filename, content_type):
            self.filename = filename
            self.content_type = content_type
            
        async def read(self):
            with open(self.filename, "rb") as f:
                return f.read()

    file = MockUploadFile("real_test_video.mp4", "video/mp4")
    
    print("Extracting media with Gemini...")
    try:
        results = await extract_text_from_file(file)
        print("--- SCENE RESULTS ---")
        for res in results:
            print("\nSCENE:")
            print(f"Timestamp: {res.get('page')}")
            print(f"Text: {res.get('text')}")
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_test())
