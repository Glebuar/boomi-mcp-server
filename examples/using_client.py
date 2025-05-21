"""Example usage of the MCP client."""
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
