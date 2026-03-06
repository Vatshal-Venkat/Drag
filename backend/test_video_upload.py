import asyncio
import os
import time
from google import genai
from google.genai import types

def run_test():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)

    print("Uploading video...")
    uploaded_file = client.files.upload(file="real_test_video.mp4", config={'mime_type': 'video/mp4'})
    print(f"Uploaded file: {uploaded_file.name}")
    print(f"State: {uploaded_file.state}")
    
    # Wait for processing
    while uploaded_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)
        
    print(f"\nFinal State: {uploaded_file.state}")

    if uploaded_file.state.name == "FAILED":
        print("File processing failed!")
        return

    prompt = "Describe this video."
    
    print("Generating content...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, prompt]
        )
        print("Success:")
        print(response.text.strip())
    except Exception as e:
        print(f"Extraction failed: {e}")
    finally:
        print("Cleaning up file...")
        client.files.delete(name=uploaded_file.name)

if __name__ == "__main__":
    run_test()
