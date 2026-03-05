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
# 🔹 RETRIEVE TOOL
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
    docs_list = (
        kwargs.get("document_ids")
        or kwargs.get("documents")
        or kwargs.get("docs")
    )

    doc_single = (
        kwargs.get("document_id")
        or kwargs.get("id")
        or kwargs.get("document")
    )

    session_id = kwargs.get("session_id")

    final_doc_ids = []
    
    if docs_list and isinstance(docs_list, list):
        final_doc_ids.extend(docs_list)
    elif doc_single:
        final_doc_ids.append(doc_single)
    elif session_id:
        active = session_manager.get_active_documents(session_id)
        if active:
            final_doc_ids.extend(active)

    if final_doc_ids:
        return retrieve(
            query=query,
            k=k,
            document_ids=final_doc_ids,
        )

    # ----------------------------
    # 3️⃣ Global fallback
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