from typing import Dict, Callable, Any, List

from app.services.retriever import retrieve, retrieve_for_comparison
from app.services.reranker import rerank_contexts
from app.agents.search_agent import SearchAgent
from app.mcp.mcp_client import MCPClient


_TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_tool(name: str):
    def decorator(fn: Callable[..., Any]):
        _TOOL_REGISTRY[name] = fn
        return fn
    return decorator


# =========================================================
# 🔹 RETRIEVE TOOL (FIXED MULTI-DOC SUPPORT)
# =========================================================

@register_tool("retrieve")
def _retrieve_tool(**kwargs):

    from app.core.session_manager import session_manager

    # ----------------------------
    # 1️⃣ Normalize Query
    # ----------------------------
    query = (
        kwargs.get("query")
        or kwargs.get("text")
        or kwargs.get("q")
    )

    if not query:
        return []

    k = kwargs.get("k", 5)

    # ----------------------------
    # 2️⃣ Normalize Document Keys
    # ----------------------------
    document_id = (
        kwargs.get("document_id")
        or kwargs.get("id")
        or kwargs.get("document")
    )

    documents = (
        kwargs.get("documents")
        or kwargs.get("docs")
    )

    session_id = kwargs.get("session_id")

    # ----------------------------
    # 3️⃣ If specific single doc
    # ----------------------------
    if document_id:
        return retrieve(
            query=query,
            k=k,
            document_id=document_id,
        )

    # ----------------------------
    # 4️⃣ Multi-doc list
    # ----------------------------
    if documents and isinstance(documents, list):
        merged = []
        for doc in documents:
            merged.extend(
                retrieve(query=query, k=k, document_id=doc)
            )
        return merged

    # ----------------------------
    # 5️⃣ Active session docs
    # ----------------------------
    if session_id:
        active_docs = session_manager.get_active_documents(session_id)
        if active_docs:
            merged = []
            for doc in active_docs:
                merged.extend(
                    retrieve(query=query, k=k, document_id=doc)
                )
            return merged

    # ----------------------------
    # 6️⃣ Global fallback
    # ----------------------------
    return retrieve(query=query, k=k)

# =========================================================
# 🔹 RERANK TOOL
# =========================================================

@register_tool("rerank")
def _rerank_tool(**kwargs):
    return rerank_contexts(**kwargs)


# =========================================================
# 🔹 SEARCH TOOL
# =========================================================

@register_tool("search")
def _search_tool(**kwargs):
    agent = SearchAgent()
    return agent.run(**kwargs)


# =========================================================
# 🔹 MCP REGISTRATION
# =========================================================

def register_mcp_tools():
    client = MCPClient()
    tools = client.discover_tools()
    for name, fn in tools.items():
        _TOOL_REGISTRY[name] = fn


def get_tool(name: str) -> Callable[..., Any] | None:
    return _TOOL_REGISTRY.get(name)


def list_tools() -> list[str]:
    return list(_TOOL_REGISTRY.keys())


# Auto-register MCP on import
register_mcp_tools()