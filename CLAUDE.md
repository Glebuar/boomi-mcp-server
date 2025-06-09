# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server that exposes Boomi API operations as tools using FastMCP. The server provides over 100 tools for managing Boomi platform resources including components, packages, deployments, environments, atoms, and various connector configurations.

## Development Commands

**Setup (Local Development):**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# or .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies for testing
pip install pytest pytest-cov ruff
```

**Running the server:**
```bash
# stdio mode (for Claude Desktop/Cursor integration)
python -m boomi_mcp_server.server

# SSE mode (HTTP server on port 8080)
python -m boomi_mcp_server.server --transport sse --port 8080
```

**Docker (Recommended for Production):**
```bash
# Build image
docker build -t boomi-mcp-server .

# Run with docker-compose
docker-compose up -d

# Run directly
docker run -p 8080:8080 --env-file .env boomi-mcp-server

# Check logs
docker logs boomi-mcp-server

# Check if container is running
docker ps | grep boomi-mcp-server
```

**Testing and Quality:**
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_server.py::test_specific_function

# Run with coverage
pytest --cov=boomi_mcp_server

# Lint code
ruff check .

# Check examples
python scripts/check_examples.py
```

## Architecture

**Core Components:**
- `src/boomi_mcp_server/server.py` - Main entry point, CLI handling, FastMCP server setup
- `src/boomi_mcp_server/tools.py` - All MCP tool definitions (100+ Boomi operations)
- `src/boomi_mcp_server/auth.py` - Boomi authentication handling
- `src/boomi_mcp_server/custom_session.py` - Custom session management for API calls
- `src/boomi_mcp_client/client.py` - Python client library for programmatic access

**Authentication Flow:**
The server requires three environment variables set before startup:
- `BOOMI_ACCOUNT` - Boomi account ID
- `BOOMI_USER` - Boomi username
- `BOOMI_SECRET` - Boomi password/secret

These are loaded via python-dotenv and used to authenticate with the Boomi API through the custom session handler.

**Tool Organization:**
Tools in `tools.py` are organized by Boomi resource type:
- Component operations (create, update, delete, get, query)
- Package management (create, deploy)
- Folder operations
- Environment and atom management
- Execution monitoring and logs
- Schedule management
- Extension management
- Connector-specific queries (AS2, EDI, HL7, OFTP2, etc.)

Each tool is decorated with `@mcp_server.tool()` and includes proper input/output type annotations using Pydantic models.

**Transport Modes:**
1. **stdio mode** - Default mode for integration with Claude Desktop, Cursor, or other MCP clients
2. **SSE mode** - HTTP server mode exposing the MCP protocol over Server-Sent Events on port 8080

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

**Workflows:**
- `ci.yml` - Runs tests, linting, and Docker build verification on every push
- `docker-publish.yml` - Builds and publishes Docker images to GitHub Container Registry (ghcr.io)
- `lint-examples.yml` - Validates example configuration files

**Docker Image:**
- Published to: `ghcr.io/glebuar/boomi-mcp-server:latest`
- Multi-stage build with non-root user for security
- Includes health check using process verification
- Based on `python:3.11-slim` with minimal dependencies

## Key Dependencies

- `boomi` - Boomi Python SDK (auto-generated from OpenAPI spec)
- `fastmcp` - MCP server framework
- `pydantic` - Data validation and settings management
- `python-dotenv` - Environment variable loading
- `uvicorn` - ASGI server for SSE mode

## Important Notes

- The SSE endpoint (`http://localhost:8080/sse`) expects Server-Sent Events protocol, not regular HTTP requests
- The `.well-known/mcp.json` file is for static MCP client discovery (used during configuration) but is not served by the running server
- When running locally, ensure `PYTHONPATH=src` is set if running outside of Docker
- The server gracefully handles unsupported MCP requests via the custom session handler