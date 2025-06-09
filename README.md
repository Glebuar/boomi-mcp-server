# Boomi MCP Server

[![CI](https://github.com/glebuar/boomi-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/glebuar/boomi-mcp-server/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://github.com/glebuar/boomi-mcp-server/pkgs/container/boomi-mcp-server)
[![License](https://img.shields.io/github/license/glebuar/boomi-mcp-server.svg)](LICENSE)

This repository provides a simple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for interacting with the Boomi API. The server exposes Boomi SDK operations as MCP tools using [FastMCP](https://pypi.org/project/fastmcp/).

## Table of Contents

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Running via Docker](#running-via-docker)
- [Running from Source](#running-from-source)
- [Cursor/Claude Setup](docs/cursor_setup.md)
- [Running tests](#running-tests)
- [Contributing](#contributing)

## Requirements

- Python 3.10+
- Access credentials for the Boomi API

## Quick start

The recommended way to run the Boomi MCP Server is using Docker:

```bash
# Pull the latest image
docker pull ghcr.io/glebuar/boomi-mcp-server:latest

# Run with environment variables
docker run -d --name boomi-mcp-server -p 8080:8080 \
  -e BOOMI_ACCOUNT=your_account \
  -e BOOMI_USER=your_user \
  -e BOOMI_SECRET=your_secret \
  ghcr.io/glebuar/boomi-mcp-server:latest
```

Alternatively, you can build from source:

```bash
git clone https://github.com/glebuar/boomi-mcp-server.git
cd boomi-mcp-server
docker build -t boomi-mcp-server .
docker run -p 8080:8080 --env-file .env boomi-mcp-server
```

## Usage

Set your Boomi credentials using environment variables or a `.env` file
(copy the provided `.env.example` and fill in your values):

```bash
BOOMI_ACCOUNT=...
BOOMI_USER=...
BOOMI_SECRET=...
```

If a `.env` file exists in the working directory the server will load it automatically.

### Using the Python client

A Python client is available in the `src/boomi_mcp_client` directory for programmatic access:

```python
import sys
sys.path.append('src')
from boomi_mcp_client import MCPClient

client = MCPClient("http://localhost:8080")
print(client.list_tools())
result = client.call_tool("health_check")
print(result)
```

See [`examples/using_client.py`](examples/using_client.py) for a complete script
demonstrating these calls.


## Running via Docker

Docker is the recommended way to run the Boomi MCP Server for production use:

### Using Docker Compose (Recommended)

1. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit .env with your Boomi credentials
   ```

2. Start the server:
   ```bash
   docker-compose up -d
   ```

3. Check if server is running:
   ```bash
   docker ps | grep boomi-mcp-server
   ```

### Using Docker directly

```bash
# Build the image
docker build -t boomi-mcp-server .

# Run with environment variables
docker run -d \
  --name boomi-mcp-server \
  -p 8080:8080 \
  -e BOOMI_ACCOUNT=your_account \
  -e BOOMI_USER=your_user \
  -e BOOMI_SECRET=your_secret \
  boomi-mcp-server

# Or use an env file
docker run -d \
  --name boomi-mcp-server \
  -p 8080:8080 \
  --env-file .env \
  boomi-mcp-server
```

### Docker Features

- **Non-root user**: Runs as unprivileged user for security
- **Health checks**: Built-in health monitoring
- **Optimized layers**: Efficient caching for faster rebuilds
- **Production ready**: Includes all necessary runtime dependencies

## Running from Source

For development or when you need to run the server locally without Docker:

### Prerequisites

- Python 3.10+
- pip or uv package manager

### Setup

```bash
git clone https://github.com/glebuar/boomi-mcp-server.git
cd boomi-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# or .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the server

```bash
# stdio mode (for Cursor/Claude Desktop integration)
python -m boomi_mcp_server.server

# SSE mode (HTTP server on port 8080)
python -m boomi_mcp_server.server --transport sse --port 8080
```

### Integration with Claude Desktop

For Claude Desktop integration, add this to your `claude_desktop_config.json`:

```jsonc
{
  "mcpServers": {
    "boomi": {
      "command": "python",
      "args": [
        "-m",
        "boomi_mcp_server.server"
      ],
      "cwd": "/path/to/boomi-mcp-server",
      "env": {
        "BOOMI_ACCOUNT": "your_account",
        "BOOMI_USER": "your_user",
        "BOOMI_SECRET": "your_secret"
      }
    }
  }
}
```

## Features

The server exposes 85+ tools covering the complete Boomi integration lifecycle:

### Core Workflow Support
- **Discovery**: Query components, environments, atoms, and folders
- **Development**: Create/update components, manage folders
- **Packaging**: Create versioned packages for deployment
- **Deployment**: Deploy packages, check deployment status
- **Execution**: Run processes with parameters, manage attachments
- **Monitoring**: Query executions, view logs, track performance
- **Debugging**: Access detailed logs, artifacts, and error records
- **Management**: Handle schedules, properties, extensions

### Connector Support
- AS2, EDI (X12/EDIFACT), HL7, OFTP2, RosettaNet, Tradacoms
- Query connector records and retrieve artifacts
- Manage connector configurations

### Advanced Features
- Process-atom attachments for execution
- Environment-atom attachments
- Queue management and listener control
- Audit logs and system events
- Document rerun capabilities
- Runtime restart management

See [docs/cursor_setup.md](docs/cursor_setup.md) for instructions on setting up
the server with Cursor/Claude Desktop.

## Development

### Running tests

To run tests, you'll need to install development dependencies:

```bash
# Clone the repository
git clone https://github.com/glebuar/boomi-mcp-server.git
cd boomi-mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov ruff

# Run tests
pytest

# Run linter
ruff check .
```

## Contributing

Please open an issue or pull request if you encounter problems or have
improvements. Ensure `pytest` and `ruff` pass before submitting changes.
