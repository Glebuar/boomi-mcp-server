from pathlib import Path
import json

from boomi_mcp.tools import mcp


def main() -> None:
    """Generate the discovery file from the FastMCP registry."""
    specs = {"tools": mcp.get_tool_specs()}
    path = Path(".well-known/mcp.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(specs, indent=2))


if __name__ == "__main__":
    main()
