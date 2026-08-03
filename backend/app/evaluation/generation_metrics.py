# backend/app/evaluation/generation_metrics.py
"""
Generation and Reasoning evaluation metrics for RAG systems:
- Faithfulness (Groundedness in context)
- Answer Relevancy (Addressing the query)
- Answer Correctness (Fact & semantic match against ground truth)
- Chain of Thought (CoT) Reasoning Quality & Verification
"""

import re
import math
from typing import List, Dict, Optional, Any, Union, Set


def _clean_text(text: str) -> str:
    """Helper to clean and normalize text for token comparison."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _get_words(text: str) -> Set[str]:
    cleaned = _clean_text(text)
    return set(w for w in cleaned.split() if len(w) > 2)


def calculate_faithfulness(
    generated_answer: str,
    retrieved_contexts: List[str],
    llm_evaluator: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calculate Faithfulness (Groundedness).
    Measures if claims in generated_answer are supported strictly by retrieved_contexts.
    
    Returns a dict with:
      - 'score': float (0.0 to 1.0)
      - 'supported_claims_count': int
      - 'total_claims_count': int
      - 'reason': str
    """
    if not generated_answer or not generated_answer.strip():
        return {"score": 0.0, "supported_claims_count": 0, "total_claims_count": 0, "reason": "Empty generated answer"}

    full_context = " ".join(retrieved_contexts)
    if not full_context.strip():
        return {"score": 0.0, "supported_claims_count": 0, "total_claims_count": 0, "reason": "No retrieved context provided"}

    # Extract sentences as claims
    raw_sentences = re.split(r"(?<=[.!?])\s+", generated_answer.strip())
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]

    if not sentences:
        return {"score": 1.0, "supported_claims_count": 0, "total_claims_count": 0, "reason": "No evaluation sentences found"}

    context_words = _get_words(full_context)

    supported_count = 0
    for stmt in sentences:
        stmt_words = _get_words(stmt)
        if not stmt_words:
            supported_count += 1
            continue
        
        # Check overlap: what percentage of key terms in sentence exist in context
        overlap = len(stmt_words.intersection(context_words)) / len(stmt_words)
        if overlap >= 0.4:  # Threshold for groundedness heuristic
            supported_count += 1

    score = float(supported_count / len(sentences))
    return {
        "score": round(score, 4),
        "supported_claims_count": supported_count,
        "total_claims_count": len(sentences),
        "reason": f"{supported_count}/{len(sentences)} sentence claims grounded in context.",
    }


def calculate_answer_relevancy(
    user_query: str,
    generated_answer: str,
    llm_evaluator: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calculate Answer Relevancy.
    Measures whether the generated answer directly addresses the user query.
    
    Returns a dict with:
      - 'score': float (0.0 to 1.0)
      - 'reason': str
    """
    if not user_query or not generated_answer:
        return {"score": 0.0, "reason": "Query or answer is empty"}

    query_words = _get_words(user_query)
    answer_words = _get_words(generated_answer)

    if not query_words or not answer_words:
        return {"score": 0.0, "reason": "Insufficient text tokens for analysis"}

    # Keyword coverage of query terms in generated answer
    overlap = len(query_words.intersection(answer_words)) / len(query_words)
    
    # Sentence length sanity check (answers shouldn't be 2 words unless short query)
    length_penalty = min(1.0, len(answer_words) / 5.0)

    score = min(1.0, (overlap * 0.7 + length_penalty * 0.3))
    return {
        "score": round(score, 4),
        "query_term_coverage": round(overlap, 4),
        "reason": f"Answer contains {len(query_words.intersection(answer_words))}/{len(query_words)} query key concepts.",
    }


def calculate_answer_correctness(
    generated_answer: str,
    reference_answer: str,
    llm_evaluator: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Calculate Answer Correctness.
    Compares the generated response against a ground-truth reference answer.
    
    Returns a dict with:
      - 'score': float (0.0 to 1.0)
      - 'factual_similarity': float
      - 'semantic_overlap': float
      - 'reason': str
    """
    if not generated_answer or not reference_answer:
        return {
            "score": 0.0,
            "factual_similarity": 0.0,
            "semantic_overlap": 0.0,
            "reason": "Missing generated or reference answer",
        }

    gen_words = _get_words(generated_answer)
    ref_words = _get_words(reference_answer)

    if not ref_words:
        return {"score": 1.0, "factual_similarity": 1.0, "semantic_overlap": 1.0, "reason": "Empty reference answer"}

    intersection = gen_words.intersection(ref_words)
    union = gen_words.union(ref_words)

    jaccard_sim = len(intersection) / len(union) if union else 0.0
    ref_recall = len(intersection) / len(ref_words)

    score = 0.5 * jaccard_sim + 0.5 * ref_recall
    return {
        "score": round(score, 4),
        "factual_similarity": round(ref_recall, 4),
        "semantic_overlap": round(jaccard_sim, 4),
        "reason": f"Jaccard similarity: {round(jaccard_sim, 2)}, Reference recall: {round(ref_recall, 2)}",
    }


def calculate_chain_of_thought_quality(
    reasoning_trace: str,
    retrieved_contexts: List[str],
    final_answer: str,
) -> Dict[str, Any]:
    """
    Evaluates Chain of Thought (CoT) reasoning quality and step consistency.
    Checks:
      1. Structural step breakdown (Presence of reasoning markers: 'first', 'because', 'therefore', 'step', etc.)
      2. Context grounding of reasoning steps.
      3. Alignment between final reasoning conclusion and the final answer.
    """
    if not reasoning_trace or not reasoning_trace.strip():
        return {
            "score": 0.0,
            "has_cot_structure": False,
            "context_grounding_score": 0.0,
            "conclusion_alignment_score": 0.0,
            "reason": "No Chain of Thought reasoning trace detected",
        }

    trace_cleaned = reasoning_trace.strip()

    # 1. Structural reasoning check
    reasoning_indicators = [
        "step", "first", "second", "next", "therefore", "because",
        "since", "consequently", "given that", "analysis", "implies"
    ]
    words_in_trace = set(_clean_text(trace_cleaned).split())
    matches = sum(1 for ind in reasoning_indicators if ind in words_in_trace)
    has_cot_structure = matches >= 2 or len(trace_cleaned.split("\n")) >= 2

    # 2. Context grounding of reasoning trace
    full_context = " ".join(retrieved_contexts)
    context_words = _get_words(full_context)
    trace_words = _get_words(trace_cleaned)

    if trace_words and context_words:
        grounding_score = len(trace_words.intersection(context_words)) / len(trace_words)
    else:
        grounding_score = 0.0

    # 3. Conclusion alignment with final answer
    answer_words = _get_words(final_answer)
    if trace_words and answer_words:
        alignment_score = len(trace_words.intersection(answer_words)) / len(answer_words)
    else:
        alignment_score = 0.0

    overall_score = (
        (0.3 if has_cot_structure else 0.0)
        + (0.4 * min(1.0, grounding_score * 1.5))
        + (0.3 * min(1.0, alignment_score * 1.5))
    )

    return {
        "score": round(min(1.0, overall_score), 4),
        "has_cot_structure": has_cot_structure,
        "context_grounding_score": round(grounding_score, 4),
        "conclusion_alignment_score": round(alignment_score, 4),
        "reason": f"CoT structured: {has_cot_structure}, Grounding: {round(grounding_score, 2)}, Answer alignment: {round(alignment_score, 2)}",
    }


def evaluate_generation(
    user_query: str,
    generated_answer: str,
    retrieved_contexts: List[str],
    reference_answer: Optional[str] = None,
    reasoning_trace: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Comprehensive evaluation of RAG Generation & Reasoning quality.
    Computes Faithfulness, Answer Relevancy, Answer Correctness, and CoT Quality.
    """
    faithfulness = calculate_faithfulness(generated_answer, retrieved_contexts)
    relevancy = calculate_answer_relevancy(user_query, generated_answer)
    
    correctness = None
    if reference_answer:
        correctness = calculate_answer_correctness(generated_answer, reference_answer)

    cot_quality = None
    if reasoning_trace:
        cot_quality = calculate_chain_of_thought_quality(reasoning_trace, retrieved_contexts, generated_answer)

    # Composite RAG triad score
    triad_scores = [faithfulness["score"], relevancy["score"]]
    if correctness:
        triad_scores.append(correctness["score"])

    rag_triad_score = sum(triad_scores) / len(triad_scores)

    return {
        "rag_triad_score": round(rag_triad_score, 4),
        "faithfulness": faithfulness,
        "answer_relevancy": relevancy,
        "answer_correctness": correctness,
        "chain_of_thought_quality": cot_quality,
    }
