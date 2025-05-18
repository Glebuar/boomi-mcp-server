# Boomi MCP Server

This repository provides a simple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for interacting with the Boomi API. The server exposes Boomi SDK operations as MCP tools using [FastMCP](https://pypi.org/project/fastmcp/).

## Requirements

- Python 3.10+
- Access credentials for the Boomi API

Install dependencies with `pip` or any PEP 517 build frontend:

```bash
pip install -e .
```

## Usage

Set your Boomi credentials as environment variables:

```bash
export BOOMI_ACCOUNT=...
export BOOMI_USER=...
export BOOMI_SECRET=...
```

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