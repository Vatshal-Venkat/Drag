# 🗺️ Architectural Specification: Topic-Clustered Logging & Telemetry

> **Status**: Recommended Architectural Roadmap (Future Release)  
> **Target Module**: `backend/app/analytics/topic_logger.py`  
> **Platform**: Drag RAG Accelerator  

---

## 1. Overview & Objective

Standard RAG logging records sequential events (timestamps, user prompts, retrieved chunk IDs, latencies, and generation outputs). While useful for immediate debugging, sequential text logs make it difficult for enterprise administrators to analyze macro-level retrieval performance across different domain topics.

**Topic-Clustered Logging** is an advanced LLMOps telemetry architecture designed to:
1. Automatically group incoming user queries into **semantic topic clusters** (e.g. using query embeddings + K-Means / HDBSCAN / BERTopic).
2. Track key RAG evaluation metrics (**Hit Rate@K**, **MRR@K**, **Faithfulness**, **Confidence**) **per topic cluster** over time.
3. Detect **Knowledge Gaps** automatically when a query cluster exhibits high volume but consistently low retrieval confidence or low Hit Rate.

---

## 2. Proposed System Architecture

```
                       ┌────────────────────────┐
                       │ User Query Ingest      │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │ Vector Embedding Engine│
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Online Classifier /   │
                       │  K-Means Clustering    │
                       └───────────┬────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       ┌────────────────────────┐    ┌────────────────────────┐
       │ Topic Cluster Assign   │    │ Knowledge Gap Detector │
       │ (e.g., "Legal Terms")  │    │ (Hit Rate < 0.70?)     │
       └────────────┬───────────┘    └────────────┬───────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │ Aggregated Telemetry   │
                       │ Dashboard & Alerts     │
                       └────────────────────────┘
```

---

## 3. Key Components & Workflow

### 3.1 Query Embedding & Vectorization
Upon receiving a user query $q$, the system computes its vector embedding $E(q) \in \mathbb{R}^d$ using the existing embedding service (`app.services.embeddings`).

### 3.2 Dynamic Topic Clustering Engine
* **Offline / Batch Mode**: Periodically runs unsupervised clustering (K-Means or HDBSCAN) over historical query logs ($N$ recent queries) to discover $C$ centroid topics.
* **Online Matching Mode**: Compares new incoming query vector $E(q)$ against existing cluster centroids using Cosine Similarity:
  $$\text{Cluster}(q) = \arg\max_{c \in C} \cos(E(q), \mathbf{\mu}_c)$$
  If maximum similarity $< \theta_{\text{threshold}}$, the query is flagged as an unclustered / novel topic.

### 3.3 Metric Aggregation Per Cluster
The system calculates real-time telemetry metrics per topic cluster $c$:

$$\text{Hit Rate}(c) = \frac{1}{|Q_c|} \sum_{q \in Q_c} \text{Hit Rate}(q)$$
$$\text{MRR}(c) = \frac{1}{|Q_c|} \sum_{q \in Q_c} \text{MRR}(q)$$
$$\text{Mean Confidence}(c) = \frac{1}{|Q_c|} \sum_{q \in Q_c} \text{Final Retrieval Score}(q)$$

---

## 4. Key Use Cases for Drag

### A. Automatic Knowledge Gap Identification
* **Problem**: Users ask questions about proprietary company topics (e.g., *"2025 Hardware Warranty"*), but the uploaded document repository only contains 2023 manuals.
* **Topic-Clustered Alert**: The telemetry system flags topic cluster `"Hardware Warranty"` with:
  - Query Count: 45 requests/week
  - Hit Rate@5: $0.20$ (Low)
  - Mean Retrieval Score: $0.41$ (Below 0.75 threshold)
* **Outcome**: Admin is automatically notified to ingest missing 2025 warranty documentation.

### B. Per-Topic Prompt & Retriever Optimization
* Enables applying tailored retrieval parameters based on query cluster classification (e.g., increasing BM25 keyword weight to $0.6$ for technical term clusters vs $0.8$ dense vector weight for conceptual query clusters).

### C. Admin Observability Dashboard
Provides visual analytics displaying query volume heatmaps, topic breakdown pie charts, and cluster-level latency metrics.

---

## 5. Recommended Database Schema & API Endpoints

### 5.1 Data Model (`TopicLogEntry`)
```python
from pydantic import BaseModel
from typing import List, Optional, Dict

class TopicClusterMetric(BaseModel):
    cluster_id: str
    cluster_label: str  # e.g., "Financial Reports", "Legal Compliance"
    query_count: int
    mean_hit_rate: float
    mean_mrr: float
    mean_confidence: float
    knowledge_gap_alert: bool

class QueryTopicLog(BaseModel):
    query_id: str
    query_text: str
    cluster_id: str
    hit_rate: float
    mrr: float
    confidence_score: float
    timestamp: str
```

### 5.2 Planned REST Endpoints
- `GET /api/analytics/topics`: Returns list of topic clusters with aggregated metrics.
- `GET /api/analytics/knowledge-gaps`: Returns clusters flagged with poor retrieval accuracy.
- `POST /api/analytics/recluster`: Triggers background re-clustering of historic query logs.

---

## 6. Implementation Roadmap

1. **Phase 1 (Current)**: Unified RAG Evaluation module (`app.evaluation`) provides baseline metrics per query sample.
2. **Phase 2 (Next)**: Persist evaluation telemetry to `memory_store/analytics.json` or PostgreSQL.
3. **Phase 3 (Future)**: Integrate Scikit-Learn K-Means clustering background task and admin UI dashboard.
