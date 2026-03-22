from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class MCPToolResult:
    ok: bool
    data: Any = None
    error: str | None = None


class MCPServer:
    """
    Minimal MCP-style tool server.
    Registers tools and exposes them by name.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: Dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, fn: Callable[..., Any]) -> None:
        self.tools[name] = fn

    def call_tool(self, name: str, **kwargs: Any) -> MCPToolResult:
        if name not in self.tools:
            return MCPToolResult(ok=False, error=f"Unknown tool: {name}")
        try:
            result = self.tools[name](**kwargs)
            return MCPToolResult(ok=True, data=result)
        except Exception as exc:
            return MCPToolResult(ok=False, error=str(exc))


class MCPClient:
    """
    Local MCP client for calling tools exposed by MCP servers.
    """

    def __init__(self) -> None:
        self.servers: Dict[str, MCPServer] = {}

    def register_server(self, server: MCPServer) -> None:
        self.servers[server.name] = server

    def call(self, server_name: str, tool_name: str, **kwargs: Any) -> Any:
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        result = self.servers[server_name].call_tool(tool_name, **kwargs)
        if not result.ok:
            raise RuntimeError(result.error or "Unknown MCP error")
        return result.data