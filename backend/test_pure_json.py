import asyncio
import os
import json
from google import genai
from google.genai import types

def run_test():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)

    print("Test purely JSON extraction...")
    prompt = (
        "You MUST output exactly valid JSON in the following format: "
        '[{"timestamp": "00:00-00:30", "text": "Detailed description and transcript here..."}, ...]'
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=["Describe a 5 second video of a cats running", prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        text = response.text.strip()
        print(text)
        print("Success JSON: ", json.loads(text))
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    run_test()
