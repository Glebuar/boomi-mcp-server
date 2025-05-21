# Boomi MCP Server

[![CI](https://github.com/glebuar/boomi-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/glebuar/boomi-mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/boomi-mcp-server.svg)](https://pypi.org/project/boomi-mcp-server/)
[![License](https://img.shields.io/github/license/glebuar/boomi-mcp-server.svg)](LICENSE)

This repository provides a simple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for interacting with the Boomi API. The server exposes Boomi SDK operations as MCP tools using [FastMCP](https://pypi.org/project/fastmcp/).

## Table of Contents

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Running with uv (Claude for Desktop)](#running-with-uv-claude-for-desktop)
- [Running via Docker](#running-via-docker)
- [Cursor/Claude Setup](docs/cursor_setup.md)
- [Running tests](#running-tests)
- [Contributing](#contributing)

## Requirements

- Python 3.10+
- Access credentials for the Boomi API

## Quick start

Clone the repository and set up a local environment using [`uv`](https://github.com/astral-sh/uv):

```bash
git clone https://github.com/glebuar/boomi-mcp-server.git
cd boomi-mcp-server

# Install uv if it is not already available
curl -LsSf https://astral.sh/uv/install.sh | sh       # macOS/Linux
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Create a virtual environment and lock dependencies
uv venv
source .venv/bin/activate     # or .venv\Scripts\activate on Windows
uv lock
```
Running `uv lock` is a recommended step to ensure reproducible environments by locking dependencies, but it's not strictly required for basic server operation if you prefer to use the latest compatible versions.

You can also install the server directly from PyPI:

```bash
pip install boomi-mcp-server uv
# or clone & pip install -e .
```

The server depends on the `boomi` and `uvicorn` packages from PyPI. If your
environment lacks internet access, pre-build wheels or vendor these
dependencies before running the installation command.

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

The package includes a simple client library for programmatic access. After
installing `boomi-mcp-server` you can import and use `MCPClient`:

```python
from boomi_mcp_client import MCPClient

client = MCPClient("http://localhost:8080")
print(client.list_tools())
result = client.call_tool("health_check")
print(result)
```

See [`examples/using_client.py`](examples/using_client.py) for a complete script
demonstrating these calls.


## Running with uv (Claude Desktop)

`uv` provides fast cold starts and isolates dependencies in a temporary virtual environment. MCP servers started with `uv` also comply with the latest MCP specification.

Claude Desktop reads its configuration from `claude_desktop_config.json`:
`~/Library/Application Support/Claude` on macOS or `%AppData%\Claude` on Windows.
Create or edit this file to add a server entry as shown below, then restart Claude Desktop.

Add a server entry in your `mcp.json` using absolute paths only. Example configurations are available under the [`examples`](examples) folder.

Windows:

```jsonc
// mcp.json
{
  "mcpServers": {
    "boomi": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\boomi-mcp-server",
        "run",
        "boomi_mcp_server/server.py"
      ]
    }
  }
}
```

macOS/Linux:

```jsonc
// mcp.json
{
  "mcpServers": {
    "boomi": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/boomi-mcp-server",
        "run",
        "boomi_mcp_server/server.py"
      ]
    }
  }
}
```

Note: `${workspaceFolder}` is a placeholder that should be replaced with the absolute path to the `boomi-mcp-server` directory if your host application does not support this variable. Alternatively, you can use the example configurations from the `examples/` folder which use absolute paths. Only the `command` and `args` keys are supported when launching from Claude Desktop. If `uv` is not in your `PATH`, replace `uv` with the full path to the `uv` executable. Restart Claude Desktop after updating `mcp.json`.

Start the server in stdio mode (for Cursor and most hosts):

```bash
uv run boomi_mcp_server/server.py
```

For development you can run an SSE HTTP server:

```bash
uv run boomi_mcp_server/server.py -- --transport sse --port 8080
```

## Running via Docker

The repository provides a `Dockerfile` and `docker-compose.yml` for
containerized deployments. Build the image and start the server with

```bash
docker build -t boomi-mcp-server .
docker run -p 8080:8080 -e BOOMI_ACCOUNT=... -e BOOMI_USER=... -e BOOMI_SECRET=... boomi-mcp-server
```

Or use Compose:

```bash
docker-compose up
```

The container listens on port `8080` by default in SSE mode and reads Boomi
credentials from environment variables.

The server exposes most methods provided by the Boomi SDK, including helpers to:

- Manage components and packages
- Work with folders and environments
- Deploy packages and inspect execution runs
- Manage schedules and extensions
- Trigger process executions

Run `tools/list` against the server to see the full list.

A discovery file is available at `.well-known/mcp.json`. See
[docs/cursor_setup.md](docs/cursor_setup.md) for instructions on using it
with Cursor/Claude Desktop.

## Running tests

This repository contains unit tests for the server. Install the development
dependencies and run them with `pytest`:

```bash
pip install -e .[dev]      # or `uv pip install -e .[dev]`
pytest
```

## Contributing

Please open an issue or pull request if you encounter problems or have
improvements. Ensure `pytest` and `ruff` pass before submitting changes.
