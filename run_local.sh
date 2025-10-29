#!/bin/bash
# Run the local Boomi MCP server for fast development testing
# No Docker, no OAuth, just stdio MCP server

cd "$(dirname "$0")"

echo "=========================================="
echo "🚀 Starting Boomi MCP Server (Local Dev)"
echo "=========================================="
echo ""
echo "This is the LOCAL DEVELOPMENT version"
echo "No OAuth, no Docker, fast iteration"
echo ""
echo "Credentials stored in: ~/.boomi_mcp_local_secrets.json"
echo ""
echo "=========================================="
echo ""

# Run the local server
python3 server_local.py
