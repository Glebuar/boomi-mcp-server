"""Simple entry point for running the Boomi MCP server."""

import argparse
import os

import uvicorn
from boomi_mcp.tools import mcp


app = mcp.http_app()


def main() -> None:
    """Launch the MCP server."""
    parser = argparse.ArgumentParser(description="Start the Boomi MCP server")
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Address to bind (default: env HOST or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8080)),
        help="Port to listen on (default: env PORT or 8080)",
    )
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
