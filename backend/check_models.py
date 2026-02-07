from google import genai
import os

client = genai.Client(api_key="AIzaSyDSf4SE24RwaVrQQIlgsVs2EpN0a1BtHEM")

print("Listing all model names...")
try:
    for model in client.models.list():
        print(f"-> {model.name}")
except Exception as e:
    print(f"Error: {e}")