from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

print("Listing all model names...")
try:
    for model in client.models.list():
        print(f"-> {model.name}")
except Exception as e:
    print(f"Error: {e}")