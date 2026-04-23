import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    m = client.models.get(model='models/gemini-pro-latest')
    print("Name:", m.name)
    print("Methods:", m.supported_generation_methods)
    
    m2 = client.models.get(model='models/gemini-3.1-pro-preview')
    print("Name:", m2.name)
    print("Methods:", m2.supported_generation_methods)
except Exception as e:
    print("Error:", e)
