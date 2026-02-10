from typing import Dict, Callable, Any

from app.services.retriever import retrieve
from app.services.reranker import rerank_contexts
from app.agents.search_agent import SearchAgent

from app.mcp.mcp_client import MCPClient


_TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_tool(name: str):
    def decorator(fn: Callable[..., Any]):
        _TOOL_REGISTRY[name] = fn
        return fn
    return decorator


@register_tool("retrieve")
def _retrieve_tool(**kwargs):
    return retrieve(**kwargs)


@register_tool("rerank")
def _rerank_tool(**kwargs):
    return rerank_contexts(**kwargs)


@register_tool("search")
def _search_tool(**kwargs):
    agent = SearchAgent()
    return agent.run(**kwargs)


def register_mcp_tools():
    """
    Discover and register tools from MCP servers.
    """
    client = MCPClient()
    tools = client.discover_tools()
    for name, fn in tools.items():
        _TOOL_REGISTRY[name] = fn


def get_tool(name: str) -> Callable[..., Any] | None:
    return _TOOL_REGISTRY.get(name)
