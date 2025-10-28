#!/usr/bin/env python3
"""
Simplified Boomi MCP Cloud Server - Direct MCP HTTP server.

This version runs the MCP server directly in HTTP mode without FastAPI wrapper,
which is simpler and more compatible with Cloud Run.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the MCP server directly
from server import mcp

if __name__ == "__main__":
    # Cloud deployment configuration
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")

    print(f"Starting Boomi MCP Server on http://{host}:{port}{path}")

    # Run MCP server in HTTP mode
    mcp.run(
        transport="http",
        host=host,
        port=port,
        path=path
    )
