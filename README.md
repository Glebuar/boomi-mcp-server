# Boomi MCP Server

[![CI](https://github.com/glebuar/boomi-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/glebuar/boomi-mcp-server/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/boomi-mcp-server.svg)](https://pypi.org/project/boomi-mcp-server/)
[![License](https://img.shields.io/github/license/glebuar/boomi-mcp-server.svg)](LICENSE)

This repository provides a simple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for interacting with the Boomi API. The server exposes Boomi SDK operations as MCP tools using [FastMCP](https://pypi.org/project/fastmcp/).

## Requirements

- Python 3.10+
- Access credentials for the Boomi API

Install the server and the `uv` launcher from PyPI:

```bash
pip install boomi-mcp-server uv
# or clone & pip install -e .
```

The server depends on the `boomi` and `uvicorn` packages from PyPI. If your
environment lacks internet access, pre-build wheels or vendor these
dependencies before running the installation command.

## Usage

Set your Boomi credentials using environment variables or a `.env` file:

```bash
BOOMI_ACCOUNT=...
BOOMI_USER=...
BOOMI_SECRET=...
```

If a `.env` file exists in the working directory the server will load it automatically.

## Running with uv (Claude for Desktop)

`uv` provides fast cold starts and isolates dependencies in a temporary virtual environment. MCP servers started with `uv` also comply with the latest MCP specification.

Claude Desktop reads its configuration from `claude_desktop_config.json`:
`~/Library/Application Support/Claude` on macOS or `%AppData%\Claude` on Windows.
Create or edit this file to add a server entry as shown below, then restart Claude.

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
        "src/server.py"
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
        "src/server.py"
      ]
    }
  }
}
```

Only the `command` and `args` keys are supported when launching from Claude. If `uv` is not in your `PATH`, replace it with the full path returned by `where uv` (Windows) or `which uv` (macOS/Linux). Restart Claude after updating `mcp.json`.

Start the server in stdio mode (for Cursor and most hosts):

```bash
uv run src/server.py
```

For development you can run an SSE HTTP server:

```bash
uv run src/server.py -- --transport sse --port 8080
```

The server exposes most methods provided by the Boomi SDK, including helpers to:

- Manage components and packages
- Work with folders and environments
- Deploy packages and inspect execution runs
- Manage schedules and extensions
- Trigger process executions

Run `tools/list` against the server to see the full list.

A discovery file is available at `.well-known/mcp.json`. See
[docs/cursor_setup.md](docs/cursor_setup.md) for instructions on using it
with Cursor.
