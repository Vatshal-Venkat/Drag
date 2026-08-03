# backend/app/evaluation/retrieval_metrics.py
"""
Retrieval evaluation metrics for RAG systems:
- Precision@K
- Recall@K
- Hit Rate@K
- Mean Reciprocal Rank (MRR@K / Mean Reciprocal Reranking)
- Normalized Discounted Cumulative Gain (NDCG@K)
"""

import math
from typing import List, Set, Dict, Union, Optional


def calculate_precision(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int = 5,
) -> float:
    """
    Calculate Precision@K.
    Precision@K = (Number of relevant documents in top K) / K
    """
    if k <= 0 or not retrieved_ids:
        return 0.0

    relevant_set = set(relevant_ids)
    top_k = retrieved_ids[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_set)
    return float(relevant_in_top_k / k)


def calculate_recall(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int = 5,
) -> float:
    """
    Calculate Recall@K.
    Recall@K = (Number of relevant documents in top K) / (Total number of relevant documents)
    """
    relevant_set = set(relevant_ids)
    if not relevant_set or k <= 0 or not retrieved_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_set)
    return float(relevant_in_top_k / len(relevant_set))


def calculate_hit_rate(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int = 5,
) -> float:
    """
    Calculate Hit Rate@K (also known as Success Rate@K).
    Hit Rate@K = 1.0 if at least one relevant document is present in top K, else 0.0.
    """
    if k <= 0 or not retrieved_ids:
        return 0.0

    relevant_set = set(relevant_ids)
    top_k = retrieved_ids[:k]
    for doc_id in top_k:
        if doc_id in relevant_set:
            return 1.0
    return 0.0


def calculate_mrr(
    retrieved_ids: List[str],
    relevant_ids: Union[Set[str], List[str]],
    k: int = 5,
) -> float:
    """
    Calculate Reciprocal Rank (RR@K) for a single query.
    RR@K = 1 / (rank of first relevant document in top K), or 0.0 if none found.
    Mean Reciprocal Rank (MRR) is the average RR@K across multiple queries.
    """
    if k <= 0 or not retrieved_ids:
        return 0.0

    relevant_set = set(relevant_ids)
    top_k = retrieved_ids[:k]

    for rank_idx, doc_id in enumerate(top_k, start=1):
        if doc_id in relevant_set:
            return float(1.0 / rank_idx)
    return 0.0


def calculate_ndcg(
    retrieved_ids: List[str],
    relevance_scores: Union[Dict[str, float], Set[str], List[str]],
    k: int = 5,
) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG@K).
    Supports either graded relevance scores (Dict[doc_id, float])
    or binary relevance (Set/List of relevant doc_ids).
    
    Formula:
      DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
      IDCG@K = Ideal DCG@K (sorted relevance scores descending)
      NDCG@K = DCG@K / IDCG@K
    """
    if k <= 0 or not retrieved_ids:
        return 0.0

    # Convert binary relevance set to dict of {doc_id: 1.0}
    if isinstance(relevance_scores, (set, list)):
        rel_dict = {doc_id: 1.0 for doc_id in relevance_scores}
    else:
        rel_dict = relevance_scores

    if not rel_dict:
        return 0.0

    top_k = retrieved_ids[:k]

    # Calculate DCG@K
    dcg = 0.0
    for i, doc_id in enumerate(top_k, start=1):
        rel = rel_dict.get(doc_id, 0.0)
        if rel > 0:
            dcg += (math.pow(2, rel) - 1.0) / math.log2(i + 1)

    # Calculate IDCG@K (Ideal DCG@K)
    sorted_rels = sorted(rel_dict.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(sorted_rels, start=1):
        if rel > 0:
            idcg += (math.pow(2, rel) - 1.0) / math.log2(i + 1)

    if idcg == 0.0:
        return 0.0

    return float(dcg / idcg)


def evaluate_retrieval_dataset(
    dataset: List[Dict],
    k: int = 5,
) -> Dict[str, float]:
    """
    Evaluate a dataset of retrieval benchmark samples.
    Each sample dict must contain:
      - 'retrieved_ids': List[str]
      - 'relevant_ids': Set[str] or List[str] or Dict[str, float] (for NDCG)
    
    Returns average metrics across the entire dataset.
    """
    if not dataset:
        return {
            "mean_precision": 0.0,
            "mean_recall": 0.0,
            "hit_rate": 0.0,
            "mrr": 0.0,
            "mean_ndcg": 0.0,
            "total_queries": 0,
            "k": k,
        }

    total_p = 0.0
    total_r = 0.0
    total_hr = 0.0
    total_mrr = 0.0
    total_ndcg = 0.0
    n = len(dataset)

    for sample in dataset:
        retrieved = sample.get("retrieved_ids", [])
        relevant = sample.get("relevant_ids", [])
        rel_scores = sample.get("relevance_scores", relevant)

        total_p += calculate_precision(retrieved, relevant, k=k)
        total_r += calculate_recall(retrieved, relevant, k=k)
        total_hr += calculate_hit_rate(retrieved, relevant, k=k)
        total_mrr += calculate_mrr(retrieved, relevant, k=k)
        total_ndcg += calculate_ndcg(retrieved, rel_scores, k=k)

    return {
        "mean_precision": round(total_p / n, 4),
        "mean_recall": round(total_r / n, 4),
        "hit_rate": round(total_hr / n, 4),
        "mrr": round(total_mrr / n, 4),
        "mean_ndcg": round(total_ndcg / n, 4),
        "total_queries": n,
        "k": k,
    }
