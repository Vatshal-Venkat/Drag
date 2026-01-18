from app.core.llm import generate

def build_prompt(context_chunks, question):
    context = "\n\n".join(
        f"[Source {i+1}] {c['text']}"
        for i, c in enumerate(context_chunks)
    )

    return f"""
You are a factual assistant.
Use ONLY the context below.
If answer is not present, say "Not found in documents."

Context:
{context}

Question:
{question}
"""

def answer(context_chunks, question):
    prompt = build_prompt(context_chunks, question)
    return generate(prompt)
