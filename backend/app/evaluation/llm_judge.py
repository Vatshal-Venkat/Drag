# backend/app/evaluation/llm_judge.py
"""
LLM-as-a-Judge for RAG generation metrics (Groq).

Each `judge_*` helper returns a metric dict on success, or None when the judge
is unavailable / the response is malformed, so callers can fall back to the
lexical heuristics in generation_metrics.py.

Any object exposing `complete_json(system: str, user: str) -> Optional[dict]`
can be used as a judge (handy for tests).
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

# Same Llama model as chat generation unless explicitly overridden
DEFAULT_JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL") or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Keep judge prompts bounded regardless of how much context the pipeline used
MAX_CONTEXT_CHARS_PER_CHUNK = 1500
MAX_TOTAL_CONTEXT_CHARS = 8000


class LLMJudge:
    """Thin JSON-mode wrapper around the shared Groq client."""

    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        self.model = model or DEFAULT_JUDGE_MODEL
        self.temperature = temperature
        self.last_error: Optional[str] = None

    def complete_json(self, system: str, user: str) -> Optional[Dict[str, Any]]:
        try:
            # Lazy import: the Groq client is created at import time and needs GROQ_API_KEY
            from app.llm.groq import client

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Judge response is not a JSON object")
            self.last_error = None
            return parsed
        except Exception as e:
            self.last_error = str(e)
            print(f"[LLMJudge] judge call failed: {e}")
            return None


# ==========================================================
# HELPERS
# ==========================================================

def _format_contexts(contexts: List[str]) -> Tuple[str, int]:
    """Number and truncate chunks for the prompt. Returns (text, number of chunks included)."""
    blocks = []
    total = 0
    for i, ctx in enumerate(contexts):
        text = (ctx or "")[:MAX_CONTEXT_CHARS_PER_CHUNK]
        if blocks and total + len(text) > MAX_TOTAL_CONTEXT_CHARS:
            break
        blocks.append(f"[{i}] {text}")
        total += len(text)
    return "\n\n".join(blocks), len(blocks)


def _rubric_to_unit(value: Any, low: int = 1, high: int = 5) -> Optional[float]:
    """Map an integer rubric score (1-5) onto 0.0-1.0."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    v = max(low, min(high, v))
    return (v - low) / (high - low)


def _call(judge: Any, system: str, user: str) -> Optional[Dict[str, Any]]:
    if judge is None:
        return None
    try:
        return judge.complete_json(system, user)
    except Exception as e:
        print(f"[LLMJudge] judge raised: {e}")
        return None


def average_precision(relevance_flags: List[bool]) -> float:
    """
    Rank-aware context precision (as in RAGAS):
    mean of Precision@k over the ranks k that hold a relevant chunk.
    """
    hits = 0
    total = 0.0
    for k, relevant in enumerate(relevance_flags, start=1):
        if relevant:
            hits += 1
            total += hits / k
    return total / hits if hits else 0.0


# ==========================================================
# FAITHFULNESS
# ==========================================================

_FAITHFULNESS_SYSTEM = """You are a strict fact-checking judge for a retrieval-augmented generation system.
Break the ANSWER into atomic factual claims, then decide for each claim whether it is
directly supported by the CONTEXT. Use only the CONTEXT, never outside knowledge.

Verdicts:
- "supported": the context states or clearly implies the claim
- "unsupported": the context does not contain enough information
- "contradicted": the context says otherwise

Ignore greetings, hedges and questions back to the user; they are not claims.
Respond in JSON: {"claims": [{"claim": "...", "verdict": "supported|unsupported|contradicted", "reason": "..."}]}"""


def judge_faithfulness(judge: Any, answer: str, contexts: List[str]) -> Optional[Dict[str, Any]]:
    formatted, _ = _format_contexts(contexts)
    user = f"CONTEXT:\n{formatted}\n\nANSWER:\n{answer}"
    data = _call(judge, _FAITHFULNESS_SYSTEM, user)
    if not data or not isinstance(data.get("claims"), list):
        return None

    claims = [c for c in data["claims"] if isinstance(c, dict) and c.get("claim")]
    if not claims:
        return {
            "score": 1.0,
            "supported_claims_count": 0,
            "total_claims_count": 0,
            "unsupported_claims": [],
            "method": "llm",
            "reason": "Answer contains no verifiable factual claims.",
        }

    verdicts = [str(c.get("verdict", "")).lower() for c in claims]
    supported = sum(1 for v in verdicts if v == "supported")
    unsupported = [
        {"claim": c["claim"], "verdict": v, "reason": c.get("reason", "")}
        for c, v in zip(claims, verdicts)
        if v != "supported"
    ]
    return {
        "score": round(supported / len(claims), 4),
        "supported_claims_count": supported,
        "total_claims_count": len(claims),
        "unsupported_claims": unsupported,
        "method": "llm",
        "reason": f"{supported}/{len(claims)} atomic claims supported by context.",
    }


# ==========================================================
# ANSWER RELEVANCY
# ==========================================================

_RELEVANCY_SYSTEM = """You judge whether an ANSWER addresses a user's QUESTION.
Ignore factual correctness; judge only relevance and directness.

Score on a 1-5 scale:
5 = fully and directly answers the question, no filler
4 = answers the question with minor omissions or minor padding
3 = partially answers, or buries the answer in irrelevant content
2 = mostly off-topic, touches the question only tangentially
1 = does not address the question at all

Set "noncommittal" to true if the answer evades or says it cannot answer.
Respond in JSON: {"score": <1-5>, "noncommittal": <true|false>, "reason": "..."}"""


def judge_answer_relevancy(judge: Any, query: str, answer: str) -> Optional[Dict[str, Any]]:
    user = f"QUESTION:\n{query}\n\nANSWER:\n{answer}"
    data = _call(judge, _RELEVANCY_SYSTEM, user)
    if not data:
        return None
    score = _rubric_to_unit(data.get("score"))
    if score is None:
        return None
    return {
        "score": round(score, 4),
        "noncommittal": bool(data.get("noncommittal", False)),
        "method": "llm",
        "reason": str(data.get("reason", "")),
    }


# ==========================================================
# ANSWER CORRECTNESS
# ==========================================================

_CORRECTNESS_SYSTEM = """You compare a GENERATED answer with a REFERENCE (ground-truth) answer.
Split both into atomic factual statements and classify them:
- "true_positives": statements in GENERATED that are supported by REFERENCE
- "false_positives": statements in GENERATED that are absent from or contradict REFERENCE
- "false_negatives": statements in REFERENCE that GENERATED is missing
Paraphrases with the same meaning count as matches.
Respond in JSON: {"true_positives": ["..."], "false_positives": ["..."], "false_negatives": ["..."], "reason": "..."}"""


def judge_answer_correctness(judge: Any, answer: str, reference: str) -> Optional[Dict[str, Any]]:
    user = f"REFERENCE:\n{reference}\n\nGENERATED:\n{answer}"
    data = _call(judge, _CORRECTNESS_SYSTEM, user)
    if not data:
        return None

    lists = {}
    for key in ("true_positives", "false_positives", "false_negatives"):
        value = data.get(key, [])
        if not isinstance(value, list):
            return None
        lists[key] = value

    tp = len(lists["true_positives"])
    fp = len(lists["false_positives"])
    fn = len(lists["false_negatives"])
    denom = tp + 0.5 * (fp + fn)
    f1 = tp / denom if denom else 1.0

    return {
        "score": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "missing_facts": lists["false_negatives"],
        "incorrect_facts": lists["false_positives"],
        "method": "llm",
        "reason": str(data.get("reason", f"Statement F1 = {round(f1, 2)}")),
    }


# ==========================================================
# CONTEXT RELEVANCE
# ==========================================================

_CONTEXT_RELEVANCE_SYSTEM = """You judge retrieved CONTEXT chunks for a user QUESTION.
For each numbered chunk, decide whether it contains information useful for answering the question.
Respond in JSON: {"verdicts": [{"index": <chunk number>, "relevant": <true|false>, "reason": "..."}]}
Return exactly one verdict per chunk, in order."""


def judge_context_relevance(judge: Any, query: str, contexts: List[str]) -> Optional[Dict[str, Any]]:
    # Only chunks that fit in the prompt get judged
    formatted, judged_count = _format_contexts(contexts)

    user = f"QUESTION:\n{query}\n\nCONTEXT:\n{formatted}"
    data = _call(judge, _CONTEXT_RELEVANCE_SYSTEM, user)
    if not data or not isinstance(data.get("verdicts"), list):
        return None

    flags = [False] * judged_count
    for v in data["verdicts"]:
        if not isinstance(v, dict):
            continue
        try:
            idx = int(v.get("index"))
        except (TypeError, ValueError):
            continue
        if 0 <= idx < judged_count:
            flags[idx] = bool(v.get("relevant", False))

    if not flags:
        return None

    relevant = sum(flags)
    return {
        "score": round(relevant / len(flags), 4),
        "context_precision": round(average_precision(flags), 4),
        "relevant_chunks": relevant,
        "total_chunks": len(flags),
        "relevance_flags": flags,
        "method": "llm",
        "reason": f"{relevant}/{len(flags)} retrieved chunks judged relevant.",
    }


# ==========================================================
# CHAIN OF THOUGHT
# ==========================================================

_COT_SYSTEM = """You audit a REASONING trace that led to a FINAL ANSWER, given the CONTEXT it was allowed to use.
Score each dimension on a 1-5 scale:
- "logical_validity": each step follows from the previous ones without leaps or fallacies
- "grounding": premises come from the CONTEXT rather than invention
- "conclusion_alignment": the FINAL ANSWER matches what the reasoning concluded
Respond in JSON: {"logical_validity": <1-5>, "grounding": <1-5>, "conclusion_alignment": <1-5>, "reason": "..."}"""


def judge_chain_of_thought(
    judge: Any, reasoning_trace: str, contexts: List[str], final_answer: str
) -> Optional[Dict[str, Any]]:
    formatted, _ = _format_contexts(contexts)
    user = (
        f"CONTEXT:\n{formatted}\n\n"
        f"REASONING:\n{reasoning_trace}\n\nFINAL ANSWER:\n{final_answer}"
    )
    data = _call(judge, _COT_SYSTEM, user)
    if not data:
        return None

    validity = _rubric_to_unit(data.get("logical_validity"))
    grounding = _rubric_to_unit(data.get("grounding"))
    alignment = _rubric_to_unit(data.get("conclusion_alignment"))
    if None in (validity, grounding, alignment):
        return None

    return {
        "score": round((validity + grounding + alignment) / 3, 4),
        "logical_validity_score": round(validity, 4),
        "context_grounding_score": round(grounding, 4),
        "conclusion_alignment_score": round(alignment, 4),
        "method": "llm",
        "reason": str(data.get("reason", "")),
    }
