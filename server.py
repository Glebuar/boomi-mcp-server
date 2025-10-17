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
import json
import sqlite3
import time
import sys
from contextlib import contextmanager
from typing import Optional, Dict
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

# --- Add boomi-python to path ---
boomi_python_path = Path(__file__).parent.parent / "boomi-python"
if boomi_python_path.exists():
    sys.path.insert(0, str(boomi_python_path))

try:
    from boomi import Boomi
except ImportError as e:
    print(f"ERROR: Failed to import Boomi SDK: {e}")
    print(f"       Boomi-python path: {boomi_python_path}")
    print(f"       Run: uv pip install git+https://github.com/Glebuar/boomi-python.git")
    sys.exit(1)

# --- Simple local secrets store (SQLite) ---
DB_PATH = os.getenv("SECRETS_DB", "secrets.sqlite")


@contextmanager
def db():
    """Database context manager with automatic schema initialization."""
    con = sqlite3.connect(DB_PATH)
    con.execute("""
    CREATE TABLE IF NOT EXISTS secrets (
        sub TEXT NOT NULL,
        profile TEXT NOT NULL,
        payload TEXT NOT NULL,
        updated_at REAL NOT NULL,
        PRIMARY KEY (sub, profile)
    )""")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def put_secret(sub: str, profile: str, payload: Dict[str, str]):
    """Store credentials for a user profile."""
    with db() as con:
        con.execute(
            "REPLACE INTO secrets (sub, profile, payload, updated_at) VALUES (?, ?, ?, ?)",
            (sub, profile, json.dumps(payload), time.time())
        )
    # Log without password
    print(f"[INFO] Stored credentials for {sub}:{profile} (username: {payload.get('username', '')[:10]}***)")


def get_secret(sub: str, profile: str) -> Dict[str, str]:
    """Retrieve credentials for a user profile."""
    with db() as con:
        cur = con.execute("SELECT payload FROM secrets WHERE sub=? AND profile=?", (sub, profile))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Profile '{profile}' not found for this user. Use set_boomi_credentials first.")
        return json.loads(row[0])


def list_profiles(sub: str):
    """List all profiles for a user."""
    with db() as con:
        cur = con.execute("SELECT profile, updated_at FROM secrets WHERE sub=?", (sub,))
        return [{"profile": p, "updated_at": ts} for (p, ts) in cur.fetchall()]


def delete_profile(sub: str, profile: str):
    """Delete a user profile."""
    with db() as con:
        cur = con.execute("DELETE FROM secrets WHERE sub=? AND profile=?", (sub, profile))
        if cur.rowcount == 0:
            raise ValueError(f"Profile '{profile}' not found.")


# --- Auth: OAuth 2.0 / OIDC ---
# Check if OAuth is enabled
OAUTH_ENABLED = os.getenv("OAUTH_ENABLED", "true").lower() in ("true", "1", "yes")

if OAUTH_ENABLED:
    try:
        from src.boomi_mcp.oauth_provider import BoomiOAuthProvider

        # Create OAuth provider from environment
        auth = BoomiOAuthProvider.from_env()

        provider_type = os.getenv("OIDC_PROVIDER", "unknown")
        print(f"[INFO] OAuth 2.0 auth configured with provider: {provider_type}")
        print(f"[INFO] Base URL: {os.getenv('OIDC_BASE_URL', 'http://localhost:8000')}")
        print(f"[INFO] OAuth endpoints:")
        print(f"       - Authorization: Navigate to /auth/login in browser")
        print(f"       - Callback: /auth/callback")
        print(f"       - Token: /token")
        print(f"[INFO] Required scopes: secrets:read, secrets:write, boomi:read")
    except Exception as e:
        print(f"[ERROR] Failed to configure OAuth: {e}")
        print("[INFO] Falling back to JWT authentication...")
        OAUTH_ENABLED = False

if not OAUTH_ENABLED:
    # Fallback to JWT for development/testing
    from fastmcp.server.auth import JWTVerifier

    JWT_ALG = os.getenv("MCP_JWT_ALG", "HS256")
    JWT_ISSUER = os.getenv("MCP_JWT_ISSUER", "https://local-issuer")
    JWT_AUDIENCE = os.getenv("MCP_JWT_AUDIENCE", "boomi-mcp")
    JWT_HS_SECRET = os.getenv("MCP_JWT_SECRET", "change-this-dev-secret")
    JWT_JWKS_URI = os.getenv("MCP_JWT_JWKS_URI")

    if JWT_ALG.startswith("HS"):
        if JWT_HS_SECRET == "change-this-dev-secret":
            print("[WARN] Using default JWT secret! Generate one with:")
            print("       python3 -c 'import secrets; print(secrets.token_urlsafe(32))'")
        auth = JWTVerifier(
            public_key=JWT_HS_SECRET,
            algorithm=JWT_ALG,
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
    else:
        if not JWT_JWKS_URI:
            print(f"[ERROR] MCP_JWT_JWKS_URI must be set for {JWT_ALG}")
            sys.exit(1)
        auth = JWTVerifier(
            jwks_uri=JWT_JWKS_URI,
            algorithm=JWT_ALG,
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )

    print(f"[INFO] JWT auth configured (fallback): {JWT_ALG} (issuer: {JWT_ISSUER})")

# Create FastMCP server with auth
mcp = FastMCP(name="boomi-mcp", auth=auth)


# --- Helper: check scope and get user info ---
def get_user_info() -> tuple[str, list[str]]:
    """Get authenticated user subject and scopes from access token."""
    token = get_access_token()
    if not token:
        raise PermissionError("Authentication required")

    # Get subject from JWT claims
    subject = token.claims.get("sub") if hasattr(token, "claims") else token.client_id
    if not subject:
        raise PermissionError("Token missing 'sub' claim")

    scopes = token.scopes
    return subject, scopes


def require(scope: str, scopes: list[str]):
    """Check if user has required scope."""
    if scope not in scopes:
        raise PermissionError(f"Missing required scope: {scope}")


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
    subject, scopes = get_user_info()
    require("secrets:write", scopes)

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
    subject, scopes = get_user_info()
    require("secrets:read", scopes)
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
    subject, scopes = get_user_info()
    require("secrets:write", scopes)

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
    subject, scopes = get_user_info()
    require("boomi:read", scopes)

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


if __name__ == "__main__":
    # Print startup info
    print("\n" + "=" * 60)
    print("🚀 Boomi MCP Server")
    print("=" * 60)

    if OAUTH_ENABLED:
        provider_type = os.getenv("OIDC_PROVIDER", "unknown")
        base_url = os.getenv("OIDC_BASE_URL", "http://localhost:8000")
        print(f"Auth Mode:     OAuth 2.0 ({provider_type})")
        print(f"Base URL:      {base_url}")
        print(f"Login URL:     {base_url}/auth/login")
    else:
        print(f"Auth Mode:     JWT ({JWT_ALG})")
        print(f"JWT Issuer:    {JWT_ISSUER}")
        print(f"JWT Audience:  {JWT_AUDIENCE}")

    print(f"Secrets DB:    {DB_PATH}")
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
    print("\nTools available:")
    print("  • set_boomi_credentials  - Store Boomi credentials")
    print("  • list_boomi_profiles    - List your profiles")
    print("  • delete_boomi_profile   - Delete a profile")
    print("  • boomi_account_info     - Get account information from Boomi API")
    print("\nRequired scopes:")
    print("  • secrets:read   - List profiles")
    print("  • secrets:write  - Store/delete credentials")
    print("  • boomi:read     - Call Boomi API")
    print("=" * 60 + "\n")

    # Streamable HTTP transport
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")

    print(f"Starting server on http://{host}:{port}{path}")
    print("Press Ctrl+C to stop\n")

    mcp.run(transport="http", host=host, port=port, path=path)
