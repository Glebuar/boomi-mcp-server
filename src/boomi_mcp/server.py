"""FastMCP server with JWT authentication and Streamable HTTP transport."""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from fastmcp import FastMCP

from .credentials import CredentialStore
from .auth import JWTAuthenticator, JWTClaims, SCOPE_SECRETS_READ, SCOPE_SECRETS_WRITE, SCOPE_BOOMI_READ
from .tools import (
    BoomiMCPTools,
    SetBoomiCredentialsInput,
    BoomiAccountInfoInput,
    DeleteBoomiProfileInput,
    TOOL_SCOPES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state (in production, use dependency injection)
credential_store: Optional[CredentialStore] = None
jwt_authenticator: Optional[JWTAuthenticator] = None
boomi_tools: Optional[BoomiMCPTools] = None
current_claims: Optional[JWTClaims] = None


def initialize_server():
    """Initialize server components."""
    global credential_store, jwt_authenticator, boomi_tools

    logger.info("Initializing Boomi MCP Server...")

    # Initialize credential store
    db_path = os.getenv("CREDENTIALS_DB_PATH", "credentials.db")
    credential_store = CredentialStore(db_path=db_path)
    logger.info(f"Credential store initialized: {db_path}")

    # Initialize JWT authenticator
    jwt_authenticator = JWTAuthenticator()
    logger.info(f"JWT authenticator initialized: {jwt_authenticator.config.algorithm}")

    # Initialize Boomi tools
    boomi_tools = BoomiMCPTools(credential_store)
    logger.info("Boomi MCP tools initialized")


def authenticate_request(authorization_header: Optional[str]) -> JWTClaims:
    """
    Authenticate request using JWT token from Authorization header.

    Args:
        authorization_header: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Validated JWT claims

    Raises:
        ValueError: If authentication fails
    """
    if not authorization_header:
        raise ValueError("Missing Authorization header")

    if not authorization_header.startswith("Bearer "):
        raise ValueError("Invalid Authorization header format. Expected 'Bearer <token>'")

    token = authorization_header[7:]  # Remove "Bearer " prefix

    try:
        claims = jwt_authenticator.verify_token(token)
        logger.info(f"Authenticated user: {claims.subject} (scopes: {', '.join(claims.scopes)})")
        return claims
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise ValueError(f"Authentication failed: {str(e)}")


def check_authorization(claims: JWTClaims, required_scopes: list[str]):
    """
    Check if user has required scopes.

    Args:
        claims: JWT claims
        required_scopes: List of required scopes

    Raises:
        ValueError: If authorization fails
    """
    if not claims.has_all_scopes(*required_scopes):
        missing = set(required_scopes) - claims.scopes
        raise ValueError(
            f"Insufficient permissions. Missing scopes: {', '.join(missing)}"
        )


# Create FastMCP server instance
mcp = FastMCP("boomi-mcp-server")


@mcp.tool()
def set_boomi_credentials(
    profile: str,
    username: str,
    password: str,
    account_id: str,
    base_url: str = "https://api.boomi.com/api/rest/v1"
) -> dict:
    """
    Store Boomi credentials for a profile (requires 'secrets:write' scope).

    Args:
        profile: Profile name (e.g., 'sandbox', 'prod')
        username: Boomi username (e.g., BOOMI_TOKEN.user@example.com)
        password: Boomi password or API token
        account_id: Boomi account ID
        base_url: Boomi API base URL

    Returns:
        Success status and message
    """
    # Check authorization
    check_authorization(current_claims, TOOL_SCOPES["set_boomi_credentials"])

    # Call tool
    result = boomi_tools.set_boomi_credentials(
        subject=current_claims.subject,
        profile=profile,
        username=username,
        password=password,
        account_id=account_id,
        base_url=base_url
    )

    return result.model_dump()


@mcp.tool()
def list_boomi_profiles() -> dict:
    """
    List all Boomi profiles for the authenticated user (requires 'secrets:read' scope).

    Returns:
        List of profile names and count
    """
    # Check authorization
    check_authorization(current_claims, TOOL_SCOPES["list_boomi_profiles"])

    # Call tool
    result = boomi_tools.list_boomi_profiles(subject=current_claims.subject)

    return result.model_dump()


@mcp.tool()
def delete_boomi_profile(profile: str) -> dict:
    """
    Delete a Boomi profile (requires 'secrets:write' scope).

    Args:
        profile: Profile name to delete

    Returns:
        Success status and message
    """
    # Check authorization
    check_authorization(current_claims, TOOL_SCOPES["delete_boomi_profile"])

    # Call tool
    result = boomi_tools.delete_boomi_profile(
        subject=current_claims.subject,
        profile=profile
    )

    return result.model_dump()


@mcp.tool()
def boomi_account_info(profile: str, timeout: int = 30) -> dict:
    """
    Get Boomi account information (requires 'boomi:read' scope).

    Retrieves account details from Boomi API using stored credentials.

    Args:
        profile: Profile name to use for API call
        timeout: API request timeout in seconds (default: 30)

    Returns:
        Account information including ID, name, status, type, dates, and raw data
    """
    # Check authorization
    check_authorization(current_claims, TOOL_SCOPES["boomi_account_info"])

    # Call tool
    result = boomi_tools.boomi_account_info(
        subject=current_claims.subject,
        profile=profile,
        timeout=timeout
    )

    return result.model_dump()


def create_http_app():
    """
    Create ASGI app for Streamable HTTP transport.

    This app handles:
    - JWT authentication from Authorization header
    - Request routing to MCP server
    - Error handling and logging
    """
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse, Response
    from starlette.requests import Request
    from sse_starlette.sse import EventSourceResponse

    async def health_check(request: Request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "healthy",
            "service": "boomi-mcp-server",
            "version": "0.1.0"
        })

    async def mcp_endpoint(request: Request):
        """
        MCP endpoint with JWT authentication.

        Expects Authorization header: Bearer <jwt_token>
        """
        global current_claims

        try:
            # Authenticate request
            auth_header = request.headers.get("Authorization")
            current_claims = authenticate_request(auth_header)

            # Handle MCP request
            # For now, return basic info - FastMCP will handle actual protocol
            return JSONResponse({
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "boomi-mcp-server",
                        "version": "0.1.0"
                    }
                }
            })

        except ValueError as e:
            logger.warning(f"Authentication/authorization failed: {e}")
            return JSONResponse(
                {"error": str(e)},
                status_code=401
            )
        except Exception as e:
            logger.error(f"MCP request failed: {e}", exc_info=True)
            return JSONResponse(
                {"error": "Internal server error"},
                status_code=500
            )

    # Create Starlette app
    app = Starlette(
        debug=os.getenv("DEBUG", "false").lower() == "true",
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Route("/mcp", mcp_endpoint, methods=["POST"]),
        ],
    )

    return app


def main():
    """Main entry point for the MCP server."""
    import sys
    import uvicorn

    # Initialize server components
    initialize_server()

    # Check if running via STDIO or HTTP
    if "--stdio" in sys.argv:
        logger.info("Starting MCP server in STDIO mode...")
        # Run in STDIO mode for local testing
        import asyncio
        asyncio.run(mcp.run(transport="stdio"))
    else:
        # Run in HTTP mode (default)
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))

        logger.info(f"Starting MCP server on http://{host}:{port}")
        logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
        logger.info(f"Health check: http://{host}:{port}/health")

        # Create HTTP app
        app = create_http_app()

        # Run with uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )


if __name__ == "__main__":
    main()
