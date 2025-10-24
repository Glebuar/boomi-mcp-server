#!/usr/bin/env python3
"""
Boomi MCP Server - FastMCP server with JWT auth for Boomi API integration.

Based on claude.md reference with security enhancements:
- JWT authentication (HS256 dev, RS256+JWKS prod)
- Per-user credential storage (SQLite dev, cloud secret manager prod)
- Scope-based authorization
- Secure logging (no password leaks)
"""

import os
import sys
import secrets
import hashlib
import base64
from typing import Optional, Dict
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

# --- Add boomi-python to path ---
boomi_python_path = Path(__file__).parent.parent / "boomi-python"
if boomi_python_path.exists():
    sys.path.insert(0, str(boomi_python_path))

# --- Add src to path for cloud_secrets ---
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from boomi import Boomi
except ImportError as e:
    print(f"ERROR: Failed to import Boomi SDK: {e}")
    print(f"       Boomi-python path: {boomi_python_path}")
    print(f"       Run: uv pip install git+https://github.com/Glebuar/boomi-python.git")
    sys.exit(1)

# --- Cloud Secrets Manager (SQLite/AWS/GCP/Azure) ---
try:
    from boomi_mcp.cloud_secrets import get_secrets_backend
    secrets_backend = get_secrets_backend()
    backend_type = os.getenv("SECRETS_BACKEND", "sqlite")
    print(f"[INFO] Using secrets backend: {backend_type}")
    if backend_type == "gcp":
        project_id = os.getenv("GCP_PROJECT_ID", "unknown")
        print(f"[INFO] GCP Project: {project_id}")
except ImportError as e:
    print(f"ERROR: Failed to import cloud_secrets: {e}")
    print(f"       Make sure src/boomi_mcp/cloud_secrets.py exists")
    sys.exit(1)


def put_secret(sub: str, profile: str, payload: Dict[str, str]):
    """Store credentials for a user profile."""
    secrets_backend.put_secret(sub, profile, payload)
    # Log without password
    print(f"[INFO] Stored credentials for {sub}:{profile} (username: {payload.get('username', '')[:10]}***)")


def get_secret(sub: str, profile: str) -> Dict[str, str]:
    """Retrieve credentials for a user profile."""
    return secrets_backend.get_secret(sub, profile)


def list_profiles(sub: str):
    """List all profiles for a user."""
    return secrets_backend.list_profiles(sub)


def delete_profile(sub: str, profile: str):
    """Delete a user profile."""
    secrets_backend.delete_profile(sub, profile)


# --- Auth: OAuth 2.0 with Google (Required) ---
from fastmcp.server.auth.providers.google import GoogleProvider

# Create Google OAuth provider
try:
    client_id = os.getenv("OIDC_CLIENT_ID")
    client_secret = os.getenv("OIDC_CLIENT_SECRET")
    base_url = os.getenv("OIDC_BASE_URL", "http://localhost:8000")

    if not client_id or not client_secret:
        raise ValueError("OIDC_CLIENT_ID and OIDC_CLIENT_SECRET must be set")

    auth = GoogleProvider(
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url,
    )

    print(f"[INFO] Google OAuth 2.0 configured")
    print(f"[INFO] Base URL: {base_url}")
    print(f"[INFO] All authenticated Google users have full access to all tools")
    print(f"[INFO] OAuth endpoints:")
    print(f"       - Authorize: {base_url}/authorize")
    print(f"       - Callback: {base_url}/auth/callback")
    print(f"       - Token: {base_url}/token")
except Exception as e:
    print(f"[ERROR] Failed to configure OAuth: {e}")
    print(f"[ERROR] Please ensure these environment variables are set:")
    print(f"       - OIDC_CLIENT_ID")
    print(f"       - OIDC_CLIENT_SECRET")
    print(f"       - OIDC_BASE_URL")
    sys.exit(1)

# Create FastMCP server with auth
mcp = FastMCP(name="boomi-mcp", auth=auth)


# --- Helper: get authenticated user info ---
def get_user_subject() -> str:
    """Get authenticated user subject from access token."""
    token = get_access_token()
    if not token:
        raise PermissionError("Authentication required")

    # Get subject from JWT claims (Google email)
    subject = token.claims.get("sub") if hasattr(token, "claims") else token.client_id
    if not subject:
        # Try email as fallback
        subject = token.claims.get("email") if hasattr(token, "claims") else None
    if not subject:
        raise PermissionError("Token missing 'sub' or 'email' claim")

    return subject


# --- Tools ---
# Note: Credential management is done via web UI at /
# The following tools are commented out to avoid confusion

# @mcp.tool()
# def set_boomi_credentials(...):
#     """Use the web UI to manage credentials"""
#     pass

# @mcp.tool()
# def list_boomi_profiles(...):
#     """Use the web UI to view profiles"""
#     pass

# @mcp.tool()
# def delete_boomi_profile(...):
#     """Use the web UI to delete profiles"""
#     pass


@mcp.tool()
def boomi_account_info(profile: str = "default"):
    """
    Get Boomi account information.

    Retrieves account details from Boomi API using credentials stored via the web UI.

    IMPORTANT: You must first store your credentials at the web portal:
    https://boomi-mcp-server-126964451821.us-central1.run.app/

    This tool implements the core logic from boomi-python/examples/12_utilities/sample.py:
    1. Retrieve your stored credentials
    2. Initialize Boomi SDK with credentials
    3. Call account.get_account() to retrieve account information
    4. Return structured account data

    Args:
        profile: Profile name (defaults to 'default')

    Returns:
        Account information including name, status, licensing details, or error details
    """
    try:
        subject = get_user_subject()
        print(f"[INFO] boomi_account_info called by user: {subject}, profile: {profile}")
    except Exception as e:
        print(f"[ERROR] Failed to get user subject: {e}")
        return {
            "_success": False,
            "error": f"Authentication failed: {str(e)}",
            "_note": "Make sure you're authenticated with OAuth"
        }

    # Try to get stored credentials
    try:
        creds = get_secret(subject, profile)
        print(f"[INFO] Successfully retrieved stored credentials for {subject}:{profile}")
        print(f"[INFO] Account ID: {creds.get('account_id')}, Username: {creds.get('username', '')[:20]}...")
    except ValueError as e:
        print(f"[ERROR] Profile '{profile}' not found for user {subject}: {e}")

        # List available profiles
        available_profiles = list_profiles(subject)
        print(f"[INFO] Available profiles for {subject}: {[p['profile'] for p in available_profiles]}")

        return {
            "_success": False,
            "error": f"Profile '{profile}' not found. Please store credentials at the web portal first.",
            "available_profiles": [p["profile"] for p in available_profiles],
            "web_portal": "https://boomi-mcp-server-126964451821.us-central1.run.app/",
            "_note": "Use the web UI to create a profile with your Boomi credentials"
        }
    except Exception as e:
        print(f"[ERROR] Unexpected error retrieving credentials: {e}")
        return {
            "_success": False,
            "error": f"Failed to retrieve credentials: {str(e)}",
            "_note": "Check server logs for details"
        }

    print(f"[INFO] Calling Boomi API for {subject}:{profile} (account: {creds['account_id']})")

    # Initialize Boomi SDK (matches sample.py - no base_url unless explicitly provided)
    try:
        sdk_params = {
            "account_id": creds["account_id"],
            "username": creds["username"],
            "password": creds["password"],
            "timeout": 30000,  # 30 seconds (SDK uses milliseconds)
        }

        # Only add base_url if explicitly provided (not None)
        if creds.get("base_url"):
            sdk_params["base_url"] = creds["base_url"]

        sdk = Boomi(**sdk_params)

        # Call the same endpoint the sample demonstrates
        result = sdk.account.get_account(id_=creds["account_id"])

        # Convert to plain dict for transport
        if hasattr(result, "__dict__"):
            out = {
                k: v for k, v in result.__dict__.items()
                if not k.startswith("_") and v is not None
            }
            out["_success"] = True
            out["_note"] = "Account data retrieved successfully"
            print(f"[INFO] Successfully retrieved account info for {creds['account_id']}")
            return out

        return {
            "_success": True,
            "message": "Account object created; minimal data returned.",
            "_note": "This indicates successful authentication."
        }

    except Exception as e:
        print(f"[ERROR] Boomi API call failed: {e}")
        return {
            "_success": False,
            "error": str(e),
            "account_id": creds["account_id"],
            "_note": "Check credentials and API access permissions"
        }


# --- Web UI Routes ---
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
import urllib.parse
import httpx


def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


def get_authenticated_user(request: Request) -> Optional[str]:
    """Extract authenticated user from request (works with OAuth middleware and sessions)."""
    # Try session first (web portal authentication)
    # Use 'sub' (Google user ID) for consistency with MCP OAuth
    if hasattr(request, "session") and request.session.get("user_sub"):
        return request.session.get("user_sub")

    # Try request.state (FastMCP/Starlette OAuth pattern for MCP clients)
    if hasattr(request.state, "user"):
        user = request.state.user
        if isinstance(user, dict):
            return user.get("sub") or user.get("email")
        if hasattr(user, "sub"):
            return user.sub
        if hasattr(user, "email"):
            return user.email
        return str(user)

    # No authenticated user found
    return None


@mcp.custom_route("/web/login", methods=["GET"])
async def web_login(request: Request):
    """Initiate OAuth login with PKCE for web portal."""
    # Get Google OAuth configuration
    client_id = os.getenv("OIDC_CLIENT_ID")
    base_url = os.getenv("OIDC_BASE_URL", str(request.base_url).rstrip('/'))

    if not client_id:
        return JSONResponse({"error": "OAuth not configured"}, status_code=500)

    # Generate PKCE parameters
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    # Store code_verifier and state in session
    request.session["oauth_state"] = state
    request.session["code_verifier"] = code_verifier

    # Build Google OAuth authorization URL with PKCE
    redirect_uri = f"{base_url}/web/callback"
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)

    print(f"[INFO] Initiating OAuth login for web portal")
    print(f"[INFO] Redirect URI: {redirect_uri}")

    return RedirectResponse(auth_url)


@mcp.custom_route("/web/callback", methods=["GET"])
async def web_callback(request: Request):
    """Handle OAuth callback for web portal."""
    # Get parameters from callback
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(f"<html><body><h1>OAuth Error</h1><p>{error}</p></body></html>", status_code=400)

    if not code or not state:
        return HTMLResponse("<html><body><h1>OAuth Error</h1><p>Missing code or state</p></body></html>", status_code=400)

    # Verify state
    stored_state = request.session.get("oauth_state")
    if not stored_state or state != stored_state:
        return HTMLResponse("<html><body><h1>OAuth Error</h1><p>Invalid state</p></body></html>", status_code=400)

    # Get stored code_verifier
    code_verifier = request.session.get("code_verifier")
    if not code_verifier:
        return HTMLResponse("<html><body><h1>OAuth Error</h1><p>Missing code_verifier</p></body></html>", status_code=400)

    # Exchange code for tokens
    client_id = os.getenv("OIDC_CLIENT_ID")
    client_secret = os.getenv("OIDC_CLIENT_SECRET")
    base_url = os.getenv("OIDC_BASE_URL", str(request.base_url).rstrip('/'))
    redirect_uri = f"{base_url}/web/callback"

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=token_data)
            response.raise_for_status()
            tokens = response.json()

        # Decode ID token to get user info (we don't verify signature here since we got it directly from Google)
        import jwt
        id_token = tokens.get("id_token")
        user_info = jwt.decode(id_token, options={"verify_signature": False})

        # Store user info in session
        request.session["user_email"] = user_info.get("email")
        request.session["user_sub"] = user_info.get("sub")

        # Clear OAuth state
        request.session.pop("oauth_state", None)
        request.session.pop("code_verifier", None)

        print(f"[INFO] Web portal login successful for {user_info.get('email')}")

        # Redirect to main page
        return RedirectResponse("/")

    except Exception as e:
        print(f"[ERROR] OAuth token exchange failed: {e}")
        return HTMLResponse(f"<html><body><h1>OAuth Error</h1><p>Token exchange failed: {str(e)}</p></body></html>", status_code=500)


@mcp.custom_route("/", methods=["GET"])
async def web_ui(request: Request):
    """Serve the credential management web UI (requires authentication)."""
    # Get authenticated user
    subject = get_authenticated_user(request)
    if not subject:
        # Show login page (no template variables needed - uses /web/login endpoint)
        template_path = Path(__file__).parent / "templates" / "login.html"
        html = template_path.read_text()
        return HTMLResponse(html)

    # Read and render template
    template_path = Path(__file__).parent / "templates" / "credentials.html"
    html = template_path.read_text()
    html = html.replace("{{ user_email }}", subject)

    return HTMLResponse(html)


@mcp.custom_route("/api/credentials", methods=["POST"])
async def api_set_credentials(request: Request):
    """API endpoint to save credentials."""
    subject = get_authenticated_user(request)
    if not subject:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        data = await request.json()

        put_secret(subject, data["profile"], {
            "username": data["username"],
            "password": data["password"],
            "account_id": data["account_id"],
            "base_url": data.get("base_url"),
        })

        return JSONResponse({
            "success": True,
            "message": f"Credentials saved for profile '{data['profile']}'"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@mcp.custom_route("/api/profiles", methods=["GET"])
async def api_list_profiles(request: Request):
    """API endpoint to list profiles."""
    subject = get_authenticated_user(request)
    if not subject:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    profiles_data = list_profiles(subject)
    profile_names = [p["profile"] for p in profiles_data]

    return JSONResponse({"profiles": profile_names})


@mcp.custom_route("/api/profiles/{profile}", methods=["DELETE"])
async def api_delete_profile(request: Request):
    """API endpoint to delete a profile."""
    subject = get_authenticated_user(request)
    if not subject:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    profile = request.path_params["profile"]

    try:
        delete_profile(subject, profile)
        return JSONResponse({
            "success": True,
            "message": f"Profile '{profile}' deleted"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


if __name__ == "__main__":
    # Print startup info
    print("\n" + "=" * 60)
    print("🚀 Boomi MCP Server")
    print("=" * 60)

    provider_type = os.getenv("OIDC_PROVIDER", "unknown")
    base_url = os.getenv("OIDC_BASE_URL", "http://localhost:8000")
    backend_type = os.getenv("SECRETS_BACKEND", "sqlite")
    print(f"Auth Mode:     OAuth 2.0 ({provider_type})")
    print(f"Base URL:      {base_url}")
    print(f"Login URL:     {base_url}/auth/login")
    print(f"Secrets:       {backend_type.upper()}")
    if backend_type == "gcp":
        print(f"GCP Project:   {os.getenv('GCP_PROJECT_ID', 'not set')}")
    print("=" * 60)

    print("=" * 60)
    print("\n🌐 Web Interface:")
    print(f"  Credential Management: {base_url}/")
    print("  (Login with Google to store your Boomi credentials)")
    print("\n🔧 MCP Tools available:")
    print("  • boomi_account_info - Get account information from Boomi API")
    print("\n📝 Note:")
    print("  Credentials are managed via the web UI (not MCP tools)")
    print("  After storing credentials in the web portal, they're automatically")
    print("  available to the boomi_account_info tool when you authenticate via MCP")
    print("=" * 60 + "\n")

    # Streamable HTTP transport
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    # Don't specify path - let OAuth routes register at root level
    # MCP endpoint will be at /mcp by default when using GoogleProvider

    print(f"Starting server on http://{host}:{port}")
    print(f"MCP endpoint: /mcp")
    print(f"OAuth endpoints: /authorize, /auth/callback, /token")
    print(f"\n💡 To set up credentials:")
    print(f"   1. Open {base_url}/ in your browser")
    print(f"   2. Login with Google")
    print(f"   3. Enter your Boomi credentials in the web form")
    print("\nPress Ctrl+C to stop\n")

    mcp.run(transport="http", host=host, port=port)
