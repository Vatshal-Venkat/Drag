"""
Build a synthetic retrieval test set from the indexed vector stores.

For a stratified sample of chunks, Gemini writes one question that the chunk
answers. The source chunk (plus any exact / near-duplicate copies of it in any
store, since some documents were uploaded more than once) is the ground truth.

Usage (from backend/):
    venv/Scripts/python.exe scripts/build_retrieval_testset.py
Output:
    eval_data/retrieval_testset.json
"""

import json
import os
import pickle
import random
import re
import sys
import time
from datetime import datetime, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from dotenv import load_dotenv

load_dotenv(os.path.join(BACKEND, ".env"))

from google import genai
from google.genai import types

STORE_DIR = os.path.join(BACKEND, "vectorstores")
OUT_PATH = os.path.join(BACKEND, "eval_data", "retrieval_testset.json")

GEN_MODEL = "gemini-2.5-flash"
SEED = 42
MIN_CHUNK_CHARS = 300
BATCH_SIZE = 10
NEAR_DUP_JACCARD = 0.9

# Questions are generated only from these (technical, non-personal) documents.
# Every other store is still searched during the benchmark, acting as distractors.
QUESTIONS_PER_STORE = {
    "stm__notes": 10,
    "adk": 8,
    "document-echo": 8,
    "ieeeechoed": 8,
    "ids_-_unit-iv": 6,
    "ids_-_unit_i": 5,
    "csme_conference": 5,
    "r-1": 4,
    "cn_syllabus_r22": 2,
    "transformations_cv_notes": 2,
    "25d58104e": 1,
    "nlp_unit1_unit2_cheatsheet": 1,
}

PROMPT = """You are building a retrieval benchmark for a document question-answering system.
For each numbered PASSAGE below, write ONE question that a real user of the system would type,
and that this passage answers.

Rules:
- The question must be self-contained: name the specific topic so it is answerable without
  seeing the passage (never "according to the passage", "this document", "the author").
- Paraphrase: do not copy any run of more than 3 consecutive words from the passage.
- Follow the requested TYPE:
  - factual: asks for a specific fact, definition, name, number or list item
  - conceptual: asks to explain / describe how or why something works
- Set "usable" to false if the passage is a title page, table of contents, references list,
  garbled text, or too generic to support a specific question.

Return JSON: {"items": [{"index": <passage number>, "usable": <bool>, "question": "...",
"answer": "<one-sentence answer taken from the passage>"}]}

"""


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def words(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_corpus():
    corpus = []  # (store_id, chunk_id, text, page, source)
    for store_id in sorted(os.listdir(STORE_DIR)):
        meta_path = os.path.join(STORE_DIR, store_id, "meta.pkl")
        if not os.path.exists(meta_path):
            continue
        with open(meta_path, "rb") as f:
            for m in pickle.load(f):
                corpus.append((store_id, m["id"], m.get("text", ""), m.get("page"), m.get("source")))
    return corpus


def is_clean(text: str) -> bool:
    if len(text) < MIN_CHUNK_CHARS:
        return False
    alpha = sum(c.isalpha() for c in text)
    return alpha / len(text) > 0.6


def sample_chunks(corpus, rng):
    picked = []
    for store_id, n in QUESTIONS_PER_STORE.items():
        seen = set()
        candidates = []
        for c in corpus:
            if c[0] != store_id or not is_clean(c[2]):
                continue
            key = norm(c[2])
            if key in seen:  # re-uploaded copy within the same store
                continue
            seen.add(key)
            candidates.append(c)
        rng.shuffle(candidates)
        # Over-sample so unusable passages can be dropped
        picked.extend(candidates[: n + max(1, n // 2)])
        print(f"{store_id:30s} candidates={len(candidates):4d} sampled={min(len(candidates), n + max(1, n // 2))}")
    return picked


def relevant_ids_for(chunk, corpus, corpus_words):
    """Source chunk plus exact / near-duplicate copies anywhere in the corpus."""
    src_norm = norm(chunk[2])
    src_words = words(chunk[2])
    ids = []
    for (store_id, chunk_id, text, _, _), w in zip(corpus, corpus_words):
        if norm(text) == src_norm:
            ids.append(f"{store_id}:{chunk_id}")
            continue
        union = src_words | w
        if union and len(src_words & w) / len(union) >= NEAR_DUP_JACCARD:
            ids.append(f"{store_id}:{chunk_id}")
    return ids


def generate(client, batch):
    body = PROMPT
    for i, (chunk, qtype) in enumerate(batch):
        body += f"\nPASSAGE {i} (TYPE: {qtype}):\n{chunk[2][:2500]}\n"

    for attempt in range(5):
        try:
            resp = client.models.generate_content(
                model=GEN_MODEL,
                contents=body,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(resp.text).get("items", [])
        except Exception as e:
            wait = 15 * (attempt + 1)
            print(f"  generation failed ({e}); retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("Question generation failed after retries")


def main():
    rng = random.Random(SEED)
    corpus = load_corpus()
    corpus_words = [words(c[2]) for c in corpus]
    print(f"Corpus: {len(corpus)} chunks across {len({c[0] for c in corpus})} stores\n")

    sampled = sample_chunks(corpus, rng)
    # Alternate question types so both hybrid-weighting paths get exercised
    jobs = [(c, "factual" if i % 2 == 0 else "conceptual") for i, c in enumerate(sampled)]

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    generated = {}
    for start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[start : start + BATCH_SIZE]
        print(f"Generating questions {start + 1}-{start + len(batch)} of {len(jobs)}")
        for item in generate(client, batch):
            try:
                idx = int(item["index"])
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= idx < len(batch) and item.get("usable") and item.get("question"):
                generated[start + idx] = item
        time.sleep(4)

    # Keep the per-store quota, in sampled order
    per_store_count = {}
    samples = []
    for i, (chunk, qtype) in enumerate(jobs):
        item = generated.get(i)
        if not item:
            continue
        store_id = chunk[0]
        if per_store_count.get(store_id, 0) >= QUESTIONS_PER_STORE[store_id]:
            continue
        per_store_count[store_id] = per_store_count.get(store_id, 0) + 1

        q_words = words(item["question"])
        overlap = len(q_words & words(chunk[2])) / len(q_words) if q_words else 0.0
        samples.append({
            "id": f"q{len(samples) + 1:03d}",
            "query": item["question"].strip(),
            "question_type": qtype,
            "reference_answer": item.get("answer", "").strip(),
            "source_store": store_id,
            "source_chunk_id": f"{store_id}:{chunk[1]}",
            "source_page": chunk[3],
            "source_file": chunk[4],
            "relevant_ids": relevant_ids_for(chunk, corpus, corpus_words),
            "source_text": chunk[2],
            "lexical_overlap": round(overlap, 3),
        })

    out = {
        "meta": {
            "created": datetime.now(timezone.utc).isoformat(),
            "generator_model": GEN_MODEL,
            "seed": SEED,
            "corpus_chunks": len(corpus),
            "corpus_stores": len({c[0] for c in corpus}),
            "total_questions": len(samples),
            "per_store": per_store_count,
            "id_format": "<store_id>:<chunk_id>",
            "notes": "Synthetic questions; ground truth = source chunk plus exact/near-duplicate copies.",
        },
        "samples": samples,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(samples)} questions to {OUT_PATH}")
    print("Per store:", per_store_count)
    if samples:
        print("Mean lexical overlap (question words found in source):",
              round(sum(s["lexical_overlap"] for s in samples) / len(samples), 3))


if __name__ == "__main__":
    main()
