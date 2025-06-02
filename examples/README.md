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

## Python Client Examples

### Basic Client Usage

The `using_client.py` script demonstrates how to programmatically interact with the MCP server:

```bash
python using_client.py
```

This will:
- Connect to the server at http://localhost:8080
- List available tools
- Call the health_check tool
- Demonstrate error handling

### Deployment Error Checking

The `check_deployment_errors.py` script helps identify deployment errors:

```bash
python check_deployment_errors.py [server_url]
```

Features:
- Queries recent deployments (last 20)
- Identifies failed deployments
- Retrieves detailed error information
- Queries audit logs for deployment events (last 48 hours)
- Generates a comprehensive error report

### Advanced Deployment Analysis

The `deployment_error_analyzer.py` script provides advanced deployment analysis with export capabilities:

```bash
# Basic usage - analyze last 7 days of deployments
python deployment_error_analyzer.py

# Analyze last 30 days
python deployment_error_analyzer.py --days 30

# Filter by environment
python deployment_error_analyzer.py --environment "your-environment-id"

# Save results to JSON
python deployment_error_analyzer.py --output deployment_errors.json

# Analyze all deployments, not just errors
python deployment_error_analyzer.py --all

# Custom server URL
python deployment_error_analyzer.py --server http://your-server:8080/sse
```

Features:
- Configurable date range analysis
- Environment filtering
- Detailed error analysis with related component/package info
- Cross-reference with audit logs
- Export results to JSON for further analysis
- Status breakdown and error rate calculation

## Prerequisites

All Python examples require the MCP server to be running:

```bash
# Docker mode
docker run -d --name boomi-mcp -p 8080:8080 \
  -e BOOMI_ACCOUNT=your_account \
  -e BOOMI_USER=your_user \
  -e BOOMI_SECRET=your_secret \
  ghcr.io/glebuar/boomi-mcp-server:latest

# Or from source in SSE mode
python -m boomi_mcp_server.server --transport sse --port 8080
```