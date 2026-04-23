import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
import inspect

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    models = client.models.list()
    for m in models:
        print("Found Model:", m.name)
except Exception as e:
    print("Error listing:", e)
