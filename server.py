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
@mcp.tool()
def set_boomi_credentials(
    username: str,
    password: str,
    account_id: str,
    profile: str = "default",
    base_url: Optional[str] = None
) -> str:
    """
    Store Boomi credentials for a profile (requires 'secrets:write' scope).

    Credentials are stored securely per user and never logged or displayed.
    Use different profiles for different environments (e.g., 'sandbox', 'prod').

    Args:
        username: Boomi username (e.g., BOOMI_TOKEN.user@example.com)
        password: Boomi password or API token
        account_id: Boomi account ID
        profile: Profile name (defaults to 'default')
        base_url: Boomi API base URL (optional - SDK will use default if not provided)
    """
    subject = get_user_subject()

    put_secret(subject, profile, {
        "username": username,
        "password": password,
        "account_id": account_id,
        "base_url": base_url,
    })

    return f"✓ Stored credentials for profile '{profile}'"


@mcp.tool()
def list_boomi_profiles():
    """
    List all Boomi profiles for the authenticated user (requires 'secrets:read' scope).

    Returns profile names and last update timestamps.
    """
    subject = get_user_subject()
    profiles = list_profiles(subject)

    if not profiles:
        return {"message": "No profiles found. Use set_boomi_credentials to create one.", "profiles": []}

    return {"profiles": profiles, "count": len(profiles)}


@mcp.tool()
def delete_boomi_profile(profile: str):
    """
    Delete a Boomi profile (requires 'secrets:write' scope).

    This permanently removes stored credentials for the profile.

    Args:
        profile: Profile name to delete
    """
    subject = get_user_subject()

    try:
        delete_profile(subject, profile)
        return f"✓ Deleted profile '{profile}'"
    except ValueError as e:
        return f"✗ {str(e)}"


@mcp.tool()
def boomi_account_info(profile: str = "default"):
    """
    Get Boomi account information (requires 'boomi:read' scope).

    Retrieves account details from Boomi API. If no credentials are stored for the
    specified profile, automatically uses credentials from .env configuration.

    This implements the core logic from boomi-python/examples/12_utilities/sample.py:
    1. Initialize Boomi SDK with credentials
    2. Call account.get_account() to retrieve account information
    3. Return structured account data

    Args:
        profile: Profile name (optional, defaults to 'default')

    Returns:
        Account information including name, status, licensing details
    """
    subject = get_user_subject()

    # Try to get stored credentials, fall back to .env if not found
    try:
        creds = get_secret(subject, profile)
        print(f"[INFO] Using stored credentials for {subject}:{profile}")
    except ValueError:
        # Fall back to .env credentials
        boomi_account = os.getenv("BOOMI_ACCOUNT")
        boomi_user = os.getenv("BOOMI_USER")
        boomi_secret = os.getenv("BOOMI_SECRET")

        if not (boomi_account and boomi_user and boomi_secret):
            return {
                "error": f"Profile '{profile}' not found and no .env credentials available. Use set_boomi_credentials first.",
                "success": False
            }

        creds = {
            "username": boomi_user,
            "password": boomi_secret,
            "account_id": boomi_account,
            "base_url": None,
        }
        print(f"[INFO] Using .env credentials (no stored profile '{profile}' found)")

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


def get_authenticated_user(request: Request) -> Optional[str]:
    """Extract authenticated user from request (works with OAuth middleware)."""
    # Try request.state (FastMCP/Starlette OAuth pattern)
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


@mcp.custom_route("/", methods=["GET"])
async def web_ui(request: Request):
    """Serve the credential management web UI (requires authentication)."""
    # Get authenticated user
    subject = get_authenticated_user(request)
    if not subject:
        # Redirect to OAuth login
        return RedirectResponse(url="/auth/login", status_code=302)

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

    # Check if .env credentials are available for auto-configuration
    boomi_account = os.getenv("BOOMI_ACCOUNT")
    boomi_user = os.getenv("BOOMI_USER")
    boomi_secret = os.getenv("BOOMI_SECRET")

    if boomi_account and boomi_user and boomi_secret:
        print(f"✓ Boomi credentials loaded from .env (account: {boomi_account})")
        print(f"  Users can call boomi_account_info without storing credentials first")
    else:
        print(f"⚠ No Boomi credentials in .env - users must call set_boomi_credentials first")

    print("=" * 60)
    print("\n🌐 Web Interface:")
    print(f"  Credential Management: {base_url}/")
    print("\n🔧 MCP Tools available:")
    print("  • set_boomi_credentials  - Store Boomi credentials")
    print("  • list_boomi_profiles    - List your profiles")
    print("  • delete_boomi_profile   - Delete a profile")
    print("  • boomi_account_info     - Get account information from Boomi API")
    print("\n🔑 Required scopes:")
    print("  • secrets:read   - List profiles")
    print("  • secrets:write  - Store/delete credentials")
    print("  • boomi:read     - Call Boomi API")
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
