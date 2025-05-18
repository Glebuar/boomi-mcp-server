from fastmcp.contrib.fastapi import serve
from boomi_mcp.tools import mcp


def main() -> None:
    """Launch the MCP server."""
    serve(mcp, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
