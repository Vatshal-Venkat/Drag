import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
import time

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("test.txt", "w") as f:
    f.write("hello")

uploaded_file = client.files.upload(file="test.txt", config={'mime_type': "text/plain"})
print("State type:", type(uploaded_file.state))
print("State:", uploaded_file.state)
if hasattr(uploaded_file.state, "name"):
    print("State name:", uploaded_file.state.name)
