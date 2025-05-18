from pathlib import Path
import json
import asyncio

from boomi_mcp.tools import mcp


async def main() -> None:
    """Generate the discovery file from the FastMCP registry."""
    tools = await mcp.get_tools()
    specs = {
        "tools": [
            tool.to_mcp_tool(name=name).model_dump()
            for name, tool in tools.items()
        ]
    }
    path = Path(".well-known/mcp.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(specs, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
