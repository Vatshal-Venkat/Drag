import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("models.txt", "w") as f:
    for m in client.models.list():
        f.write(m.name + "\n")
