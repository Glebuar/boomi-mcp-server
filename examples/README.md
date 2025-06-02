# Boomi MCP Server Examples

This directory contains example configurations and scripts for using the Boomi MCP Server.

## Configuration Files

### Docker Configuration (Recommended)
- `mcp.json.docker` - Configuration for connecting to the server running in Docker

### Source Configuration
- `mcp.json.linux` - Configuration for running from source on Linux/macOS
- `mcp.json.windows` - Configuration for running from source on Windows

## Usage

1. **For Docker (Recommended):**
   ```bash
   # Start the Docker container
   docker run -d --name boomi-mcp -p 8080:8080 \
     -e BOOMI_ACCOUNT=your_account \
     -e BOOMI_USER=your_user \
     -e BOOMI_SECRET=your_secret \
     ghcr.io/glebuar/boomi-mcp-server:latest
   
   # Copy the Docker configuration
   cp mcp.json.docker ~/.config/Cursor/mcp.json  # For Cursor
   # or
   cp mcp.json.docker "~/Library/Application Support/Claude/claude_desktop_config.json"  # For Claude Desktop
   ```

2. **For running from source:**
   - Clone the repository
   - Install dependencies: `pip install -r requirements.txt`
   - Copy the appropriate configuration file and update paths
   - Set your Boomi credentials in the environment section

## Python Client Example

The `using_client.py` script demonstrates how to programmatically interact with the MCP server:

```python
python using_client.py
```

This will:
- Connect to the server at http://localhost:8080
- List available tools
- Call the health_check tool
- Demonstrate error handling