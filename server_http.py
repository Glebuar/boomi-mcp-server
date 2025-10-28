#!/usr/bin/env python3
"""
HTTP server wrapper for Boomi MCP Server with OAuth routes.

This properly exposes OAuth routes at root level alongside MCP endpoint.
"""

import os
import secrets
import uvicorn
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

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

    # Mount static files directory
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print(f"[INFO] Mounted static files from {static_dir}")

    # Add session middleware for web portal OAuth
    # MUST use persistent SESSION_SECRET for OAuth to work across requests
    session_secret = os.getenv("SESSION_SECRET")
    if not session_secret:
        print("[ERROR] SESSION_SECRET environment variable must be set!")
        print("[ERROR] Without a persistent SESSION_SECRET, OAuth will fail with 'Invalid state' errors")
        exit(1)

    print(f"[INFO] Configuring SessionMiddleware for web UI OAuth")
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        session_cookie="boomi_session",
        max_age=3600,  # 1 hour
        same_site="lax",
        https_only=os.getenv("OIDC_BASE_URL", "").startswith("https://"),
        path="/",
    )
    print(f"[INFO] SessionMiddleware configured (https_only={os.getenv('OIDC_BASE_URL', '').startswith('https://')})")

    # Run with uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")
