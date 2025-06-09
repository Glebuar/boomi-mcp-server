"""Example usage of the MCP client."""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from boomi_mcp_client import MCPClient

# assumes the server is running on localhost:8080 in SSE mode
# connect to the server's SSE endpoint
client = MCPClient("http://localhost:8080/sse")

# List available tools
tools = client.list_tools()
print("Available tools:", [t["name"] for t in tools])

# Call the health_check tool
result = client.call_tool("health_check")
print("Health check result:", result)
