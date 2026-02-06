from typing import Dict, Callable, Any

# ==================================================
# TOOL REGISTRY
# ==================================================

_TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {}


def register_tool(name: str):
    def decorator(fn: Callable[..., Any]):
        _TOOL_REGISTRY[name] = fn
        return fn
    return decorator


def get_tool(name: str) -> Callable[..., Any] | None:
    return _TOOL_REGISTRY.get(name)
