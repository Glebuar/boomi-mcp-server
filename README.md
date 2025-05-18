# Boomi MCP Server

This repository provides a simple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for interacting with the Boomi API. The server exposes Boomi SDK operations as MCP tools using [FastMCP](https://pypi.org/project/fastmcp/).

## Requirements

- Python 3.10+
- Access credentials for the Boomi API

Install the package directly from PyPI:

```bash
pip install boomi-mcp-server
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

Then start the server:

```bash
python server.py
```

The server exposes most methods provided by the Boomi SDK, including helpers to:

- Manage components and packages
- Work with folders and environments
- Deploy packages and inspect execution runs
- Manage schedules and extensions
- Trigger process executions

Run `tools/list` against the server to see the full list.

A discovery file is available at `.well-known/mcp.json`.
