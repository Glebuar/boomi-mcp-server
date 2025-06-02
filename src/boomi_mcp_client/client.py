from __future__ import annotations

import anyio
from fastmcp.client import Client as FastMCPClient
from typing import Any

class MCPClient:
    """Simple client for interacting with a running Boomi MCP server."""

    def __init__(self, server_url: str = "http://localhost:8080") -> None:
        self.server_url = server_url

    def list_tools(self) -> list[dict[str, Any]]:
        """Return a list of available tools from the server."""
        async def _run() -> list[dict[str, Any]]:
            async with FastMCPClient(self.server_url) as client:
                tools = await client.list_tools()
                return [tool.model_dump() for tool in tools]

        return anyio.run(_run)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> list[Any]:
        """Call a tool on the server and return its result."""
        async def _run() -> list[Any]:
            async with FastMCPClient(self.server_url) as client:
                return await client.call_tool(name, arguments or {})

        return anyio.run(_run)
