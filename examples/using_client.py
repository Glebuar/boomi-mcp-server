"""Example usage of the MCP client."""
from boomi_mcp_client import MCPClient

# assumes the server is running on localhost:8080 in SSE mode
client = MCPClient("http://localhost:8080")

# List available tools
tools = client.list_tools()
print("Available tools:", [t["name"] for t in tools])

# Call the health_check tool
result = client.call_tool("health_check")
print("Health check result:", result)
