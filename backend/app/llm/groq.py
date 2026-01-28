from groq import Groq

client = Groq()

def groq_chat(messages, model="llama3-8b-8192"):
    return client.chat.completions.create(
        model=model,
        messages=messages
    )