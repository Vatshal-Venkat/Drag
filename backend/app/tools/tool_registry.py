from typing import Dict, Callable, Any

from app.services.retriever import retrieve
from app.services.reranker import rerank_contexts
from app.agents.search_agent import search


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
    return search(**kwargs)


def get_tool(name: str) -> Callable[..., Any] | None:
    return _TOOL_REGISTRY.get(name)
