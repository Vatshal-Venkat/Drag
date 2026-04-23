import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-3.1-pro-preview',
        contents="Say hello world in json",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    print("Test passed:", response.text)
except Exception as e:
    print("Test failed:", str(e))
