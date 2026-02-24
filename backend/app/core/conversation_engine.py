from typing import List, Dict, Generator, Optional
import re
import math

from app.core.llms import summarizer_llm
from app.core.session_manager import session_manager
from app.utils.context_trimmer import trim_messages, trim_context

from app.services.retriever import (
    retrieve_context,
    retrieve_for_comparison,
    align_sections_hybrid,
)

from app.services.generator import (
    stream_answer,
    stream_aligned_comparison_answer,
    generate_sentence_citations,
)

from app.agents.planner_agent import plan_next_steps
from app.tools.tool_registry import get_tool
from app.services.embeddings import embed_query, embed_texts

# ==========================================================
# CONFIGURATION
# ==========================================================

MAX_AGENT_STEPS = 4

BASE_CONFIDENCE_THRESHOLD = 0.30
BASE_FINAL_SCORE_THRESHOLD = 0.35
DYNAMIC_THRESHOLD_BOOST = 0.05


# ==========================================================
# QUERY REWRITE (SAFE)
# ==========================================================

def rewrite_query(query: str, summary: str, messages: List[Dict]) -> str:
    conversation_context = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages[-6:]
    )

    system_prompt = """You optimize search queries for semantic retrieval.

Rules:
1. Keep concise.
2. Preserve keywords.
3. Do NOT introduce new domains.
4. If clear, return unchanged.
Return ONLY the optimized query."""

    user_prompt = f"""
Conversation Summary:
{summary}

Recent Conversation:
{conversation_context}

Original Query:
{query}

Rewritten Query:
""".strip()

    rewritten = summarizer_llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    return rewritten.strip() if rewritten else query


# ==========================================================
# DYNAMIC THRESHOLDS
# ==========================================================

def dynamic_thresholds(chunk_count: int):
    conf = BASE_CONFIDENCE_THRESHOLD
    score = BASE_FINAL_SCORE_THRESHOLD

    if chunk_count > 6:
        conf += DYNAMIC_THRESHOLD_BOOST
        score += DYNAMIC_THRESHOLD_BOOST

    return conf, score


# ==========================================================
# SEMANTIC RE-RANK
# ==========================================================

def semantic_rerank(query: str, chunks: List[Dict]) -> List[Dict]:
    if not chunks:
        return []

    query_embedding = embed_query(query)
    texts = [c.get("text", "") for c in chunks]
    chunk_embeddings = embed_texts(texts)

    def cosine(a, b):
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    for chunk, emb in zip(chunks, chunk_embeddings):
        chunk["_semantic_score"] = round(cosine(query_embedding, emb), 4)

    chunks.sort(key=lambda c: c["_semantic_score"], reverse=True)
    return chunks


# ==========================================================
# FILTER CHUNKS
# ==========================================================

def filter_chunks(chunks: List[Dict]) -> List[Dict]:
    if not chunks:
        return []

    conf_th, score_th = dynamic_thresholds(len(chunks))

    filtered = []
    for c in chunks:
        conf = float(c.get("confidence", 0))
        score = float(c.get("final_score", conf))
        if conf >= conf_th and score >= score_th:
            filtered.append(c)

    return filtered


# ==========================================================
# CONVERSATION ENGINE
# ==========================================================

class ConversationEngine:

    def stream(
        self,
        *,
        session_id: str,
        query: str,
        compare_mode: bool = False,
        document_ids: Optional[List[str]] = None,
        top_k: int = 8,
        use_human_feedback: bool = True,
    ) -> Generator[Dict, None, None]:

        session = session_manager.get_session(session_id)
        if not session:
            yield {"type": "error", "value": "Session not found"}
            return

        session_manager.append_message(
            session_id=session_id,
            role="user",
            content=query,
        )

        summary = session_manager.get_summary(session_id)
        recent_messages = session_manager.get_recent_messages(
            session_id=session_id,
            limit=20,
        )

        trimmed_messages = trim_messages(recent_messages, max_chars=6000)

        rewritten_query = rewrite_query(query, summary or "", trimmed_messages)

        print("===================================")
        print("ORIGINAL QUERY:", query)
        print("REWRITTEN QUERY:", rewritten_query)
        print("===================================")

        active_docs = (
            document_ids
            if document_ids
            else session_manager.get_active_documents(session_id)
        )

        print("ACTIVE DOCS:", active_docs)

        # ======================================================
        # IF NO DOCUMENTS → PURE CONVERSATIONAL MODE
        # ======================================================

        if not active_docs:
            print("MODE: Conversational (No active docs)")
            full_answer = ""

            for token in stream_answer(
                query=query,
                contexts=[],
                summary=summary,
                conversation_messages=trimmed_messages,
                observations=None,
                use_human_feedback=use_human_feedback,
            ):
                full_answer += token
                yield {"type": "token", "value": token}

            session_manager.append_message(
                session_id=session_id,
                role="assistant",
                content=full_answer,
            )

            yield {"type": "done"}
            return

        # ======================================================
        # COMPARE MODE
        # ======================================================

        if compare_mode and len(active_docs) >= 2:
            print("MODE: Compare")

            grouped = retrieve_for_comparison(
                query=rewritten_query,
                document_ids=active_docs,
                top_k=top_k,
            )

            for doc_id in grouped:
                filtered = filter_chunks(grouped[doc_id])
                grouped[doc_id] = semantic_rerank(rewritten_query, filtered)

            if not any(grouped.values()):
                yield {
                    "type": "token",
                    "value": "No relevant context found in uploaded documents."
                }
                yield {"type": "done"}
                return

            aligned = align_sections_hybrid(grouped)

            full_answer = ""
            for token in stream_aligned_comparison_answer(
                query=query,
                aligned_sections=aligned,
            ):
                full_answer += token
                yield {"type": "token", "value": token}

            yield {"type": "sources", "value": grouped}

            session_manager.append_message(
                session_id=session_id,
                role="assistant",
                content=full_answer,
            )

            yield {"type": "done"}
            return

        # ======================================================
        # STRICT A2A RAG LOOP
        # ======================================================

        observations: List[Dict] = []
        step_count = 0

        while step_count < MAX_AGENT_STEPS:
            step_count += 1

            plan = plan_next_steps(
                session_id=session_id,
                user_query=query,
            )

            print("AGENT PLAN:", plan)

            # If planner explicitly says chat → allow conversational fallback
            if plan.get("actions") and plan["actions"][0]["name"] == "chat":
                print("MODE: Planner Chat Fallback")
                full_answer = ""
                for token in stream_answer(
                    query=query,
                    contexts=[],
                    summary=summary,
                    conversation_messages=trimmed_messages,
                    observations=None,
                    use_human_feedback=use_human_feedback,
                ):
                    full_answer += token
                    yield {"type": "token", "value": token}

                session_manager.append_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_answer,
                )

                yield {"type": "done"}
                return

            # Force retrieve in strict RAG
            print("EXECUTING TOOL: retrieve")

            tool = get_tool("retrieve")
            if not tool:
                break

            result = tool(
                query=rewritten_query,
                document_id=active_docs[0],
                k=top_k,
            )

            
            if result:
                for r in result:
                    print("CONF:", r.get("confidence"), "| FINAL:", r.get("final_score"))
                    print("TEXT:", r.get("text", "")[:200])
                    print("-" * 60)
            else:
                print("No chunks retrieved")
            filtered = filter_chunks(result or [])
            reranked = semantic_rerank(rewritten_query, filtered)

            if not reranked:
                yield {
                    "type": "token",
                    "value": "No relevant context found in uploaded documents."
                }
                yield {"type": "done"}
                return

            observations.extend(reranked)
            break

        # ======================================================
        # GENERATE FROM STRICT CONTEXT
        # ======================================================

        trimmed_contexts, _ = trim_context(
            observations,
            max_chars=6000,
        )

        print("MODE: Strict RAG Generation")

        full_answer = ""
        for token in stream_answer(
            query=query,
            contexts=trimmed_contexts,
            summary=summary,
            conversation_messages=trimmed_messages,
            observations=None,
            use_human_feedback=use_human_feedback,
        ):
            full_answer += token
            yield {"type": "token", "value": token}

        citations = generate_sentence_citations(
            full_answer,
            trimmed_contexts,
        )

        yield {"type": "citations", "value": citations}
        yield {"type": "sources", "value": trimmed_contexts}

        session_manager.append_message(
            session_id=session_id,
            role="assistant",
            content=full_answer,
        )

        yield {"type": "done"}