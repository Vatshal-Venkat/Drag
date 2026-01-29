from groq import Groq

client = Groq()

def groq_chat(messages, model="llama-3.1-70b-versatile"):
    return client.chat.completions.create(
        model=model,
        messages=messages
    )