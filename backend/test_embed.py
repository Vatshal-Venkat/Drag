import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    from dotenv import load_dotenv
    load_dotenv("c:\\Users\\Venkat_Vatshal\\OneDrive\\Desktop\\AI-DOC\\backend\\.env")
    api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
for m in client.models.list():
    if "embed" in m.name.lower() or "multimodal" in m.name.lower():
        print(m.name)
