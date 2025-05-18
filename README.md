# Boomi MCP Server

This repository provides a simple [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server
for interacting with the Boomi API. The server exposes a few Boomi SDK
operations as MCP tools using [FastMCP](https://pypi.org/project/fastmcp/).

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

The server will listen on port `8080` and expose the MCP stdio transport and
an HTTP endpoint suitable for use with any MCP client.
