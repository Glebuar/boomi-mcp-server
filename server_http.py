#!/usr/bin/env python3
"""
HTTP server wrapper for Boomi MCP Server with OAuth routes.

This properly exposes OAuth routes at root level alongside MCP endpoint.
"""

import os
import secrets
import uvicorn
from starlette.middleware.sessions import SessionMiddleware

if __name__ == "__main__":
    # Import mcp from server module (ensures OAuth provider is initialized)
    from server import mcp

    # Get configuration from environment
    # Cloud Run provides PORT, fallback to MCP_PORT for local dev
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8080")))

    print(f"\n{'='*60}")
    print("🚀 Boomi MCP Server with Google OAuth 2.0")
    print(f"{'='*60}")
    print(f"Server:           http://{host}:{port}")
    print(f"🌐 Web UI:        http://{host}:{port}/")
    print(f"MCP endpoint:     /mcp")
    print(f"Web login:        /web/login (with PKCE)")
    print(f"Web callback:     /web/callback")
    print(f"OAuth authorize:  /authorize (for MCP clients)")
    print(f"OAuth callback:   /auth/callback (for MCP clients)")
    print(f"Token endpoint:   /token")
    print(f"Metadata:         /.well-known/oauth-authorization-server")
    print(f"{'='*60}")
    print("💡 To set up Boomi credentials:")
    print(f"   1. Open http://{host}:{port}/ in your browser")
    print("   2. Login with Google (uses PKCE for security)")
    print("   3. Enter your Boomi credentials in the web form")
    print(f"{'='*60}")
    print("For MCP clients: Use auth='oauth' when connecting")
    print(f"{'='*60}\n")

    # Create the HTTP app with all routes (MCP + OAuth)
    app = mcp.http_app()

    # Add session middleware for web portal OAuth
    # Generate a random secret key for sessions (in production, use a persistent secret)
    session_secret = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        session_cookie="boomi_session",
        max_age=3600,  # 1 hour
        same_site="lax",
        https_only=os.getenv("OIDC_BASE_URL", "").startswith("https://"),
    )

    # Run with uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")
