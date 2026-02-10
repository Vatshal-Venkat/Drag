import requests
from typing import Dict, Callable, Any

from app.core.config import MCP_ENABLED, MCP_SERVER_URLS


class MCPClient:
    """
    Minimal MCP server client.
    Discovers tools and exposes them as callable functions.
    """

    def __init__(self):
        self.servers = MCP_SERVER_URLS
        self.tools: Dict[str, Callable[..., Any]] = {}

    def discover_tools(self) -> Dict[str, Callable[..., Any]]:
        """
        Discover tools from all configured MCP servers.
        """
        if not MCP_ENABLED:
            return {}

        for server in self.servers:
            server = server.strip()
            if not server:
                continue

            try:
                response = requests.get(f"{server}/tools", timeout=5)
                response.raise_for_status()
                tools = response.json()

                for tool in tools:
                    name = tool.get("name")
                    if name:
                        self.tools[name] = self._build_tool(server, name)

            except Exception:
                # MCP must NEVER break core execution
                continue

        return self.tools

    def _build_tool(self, server: str, tool_name: str) -> Callable[..., Any]:
        def _tool(**kwargs):
            payload = {
                "tool": tool_name,
                "params": kwargs,
            }
            response = requests.post(
                f"{server}/invoke",
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            return response.json().get("result")

        return _tool
