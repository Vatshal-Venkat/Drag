import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("test.txt", "w") as f:
    f.write("hello")

try:
    f = client.files.upload(file="test.txt", config={'mime_type': "text/plain"})
    print("Success:", f.name)
except Exception as e:
    print("Failed config dict:", e)

try:
    f2 = client.files.upload(file="test.txt", config=types.UploadFileConfig(mime_type="text/plain"))
    print("Success:", f2.name)
except Exception as e:
    print("Failed types config:", e)
