from typing import List, Dict, Generator, Optional
import re
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
from app.registry.document_registry import list_documents


# ==========================================================
# SMART REACT DETECTION
# ==========================================================

_REASONING_PATTERNS = [
    r"\bwhy\b",
    r"\bhow\b",
    r"\banalyze\b",
    r"\bevaluate\b",
    r"\bexplain in detail\b",
    r"\bstep[- ]?by[- ]?step\b",
    r"\bderive\b",
    r"\binfer\b",
    r"\bimplication",
    r"\bimpact\b",
    r"\bbased on\b",
]

def rewrite_query(query: str, summary: str, messages: List[Dict]) -> str:
    """
    Rewrites user query using session memory for better retrieval.
    """

    conversation_context = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages[-6:]
    )

    system_prompt = """Rewrite the user's query to be clearer and more retrieval-optimized.
                        Keep original meaning. Expand implicit references.
                        Return ONLY the rewritten query."""
    
    user_prompt = f"""
                    Conversation Summary:
                       {summary}

                    Recent Conversation:
                    {conversation_context}
                        
                    Original Query:
                    {query}

                    Rewritten Query
                    """.strip()

    rewritten = summarizer_llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    return rewritten.strip() if rewritten else query

def should_use_react(query: str, active_docs: List[str]) -> bool:
    if not active_docs:
        return False

    if len(query.split()) < 8:
        return False

    query_lower = query.lower()

    for pattern in _REASONING_PATTERNS:
        if re.search(pattern, query_lower):
            return True

    return False


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
        top_k: int = 5,
        use_human_feedback: bool = True,
    ) -> Generator[Dict, None, None]:

        # --------------------------------------------------
        # LOAD SESSION
        # --------------------------------------------------

        session = session_manager.get_session(session_id)
        if not session:
            yield {"type": "error", "value": "Session not found"}
            return

        # Save user message immediately
        session_manager.append_message(
            session_id=session_id,
            role="user",
            content=query,
        )

        # --------------------------------------------------
        # LOAD MEMORY
        # --------------------------------------------------

        summary = session_manager.get_summary(session_id)

        recent_messages = session_manager.get_recent_messages(
            session_id=session_id,
            limit=20,
        )

        trimmed_messages = trim_messages(
            recent_messages,
            max_chars=6000,
        )

        active_docs = (
            document_ids
            if document_ids
            else session_manager.get_active_documents(session_id)
        )

        # --------------------------------------------------
        # COMPARISON MODE (BYPASS REACT)
        # --------------------------------------------------

        if compare_mode and active_docs and len(active_docs) >= 2:

            grouped_contexts = retrieve_for_comparison(
                query=query,
                top_k=top_k,
                document_ids=active_docs,
            )

            aligned_sections = align_sections_hybrid(grouped_contexts)

            full_answer = ""

            for token in stream_aligned_comparison_answer(
                query=query,
                aligned_sections=aligned_sections,
            ):
                full_answer += token
                yield {"type": "token", "value": token}

            yield {"type": "sources", "value": grouped_contexts}

            # Save assistant response
            session_manager.append_message(
                session_id=session_id,
                role="assistant",
                content=full_answer,
            )

            session_manager.maybe_update_summary(
                session_id=session_id,
                user_query=query,
                assistant_answer=full_answer,
            )

            yield {"type": "done"}
            return

        # --------------------------------------------------
        # STANDARD RETRIEVAL
        # --------------------------------------------------

        rewritten_query = rewrite_query(query, summary or "", trimmed_messages)
        print("ORIGINAL QUERY:", query)
        print("REWRITTEN QUERY:", rewritten_query)

        contexts = []

        if active_docs:
            contexts = retrieve_context(
                query=rewritten_query,
                top_k=top_k,
                document_id=active_docs[0],
            )

        trimmed_contexts, _ = trim_context(
            contexts,
            max_chars=6000,
        )

        # --------------------------------------------------
        # REACT DECISION
        # --------------------------------------------------

        use_react = should_use_react(query, active_docs)

        # (Planner integration could be added here if needed)
        # Currently relying on strong generator with full context.

        # --------------------------------------------------
        # GENERATION
        # --------------------------------------------------

        full_answer = ""

        for token in stream_answer(
            query=query,
            contexts=trimmed_contexts,
            summary=summary,
            conversation_messages=trimmed_messages,
            observations=session_manager.get_observations(session_id),
            use_human_feedback=use_human_feedback,
        ):
            full_answer += token
            yield {"type": "token", "value": token}

        # --------------------------------------------------
        # CITATIONS
        # --------------------------------------------------

        citations = generate_sentence_citations(
            full_answer,
            trimmed_contexts,
        )

        yield {"type": "citations", "value": citations}
        yield {"type": "sources", "value": trimmed_contexts}

        # --------------------------------------------------
        # SAVE MEMORY
        # --------------------------------------------------

        session_manager.append_message(
            session_id=session_id,
            role="assistant",
            content=full_answer,
        )

        session_manager.maybe_update_summary(
            session_id=session_id,
            user_query=query,
            assistant_answer=full_answer,
        )

        yield {"type": "done"}