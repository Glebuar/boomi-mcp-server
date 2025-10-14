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
from fastmcp.server.auth import JWTVerifier, AccessToken
from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field

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


# --- Auth: JWT (HS256) for dev; use JWKS/RS256 in prod ---
JWT_ALG = os.getenv("MCP_JWT_ALG", "HS256")
JWT_ISSUER = os.getenv("MCP_JWT_ISSUER", "https://local-issuer")
JWT_AUDIENCE = os.getenv("MCP_JWT_AUDIENCE", "boomi-mcp")
JWT_HS_SECRET = os.getenv("MCP_JWT_SECRET", "change-this-dev-secret")  # dev only
JWT_JWKS_URI = os.getenv("MCP_JWT_JWKS_URI")  # RS256 production

# Configure JWT verifier based on algorithm
if JWT_ALG.startswith("HS"):
    # Symmetric algorithm (HS256/384/512) - use shared secret as public_key
    if JWT_HS_SECRET == "change-this-dev-secret":
        print("[WARN] Using default JWT secret! Generate one with:")
        print("       python3 -c 'import secrets; print(secrets.token_urlsafe(32))'")
    auth = JWTVerifier(
        public_key=JWT_HS_SECRET,  # For HS* algorithms, public_key is the shared secret
        algorithm=JWT_ALG,
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )
else:
    # Asymmetric algorithm (RS256/384/512, ES256, etc.) - use JWKS
    if not JWT_JWKS_URI:
        print(f"[ERROR] MCP_JWT_JWKS_URI must be set for {JWT_ALG}")
        sys.exit(1)
    auth = JWTVerifier(
        jwks_uri=JWT_JWKS_URI,
        algorithm=JWT_ALG,
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )

print(f"[INFO] JWT auth configured: {JWT_ALG} (issuer: {JWT_ISSUER}, audience: {JWT_AUDIENCE})")

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


# --- Schemas ---
class Profile(BaseModel):
    """Profile identifier."""
    profile: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,32}$", description="Profile name")


class SetCreds(Profile):
    """Credentials for Boomi API."""
    username: str = Field(..., description="Boomi username (e.g., BOOMI_TOKEN.user@example.com)")
    password: str = Field(..., description="Boomi password or API token")
    account_id: str = Field(..., description="Boomi account ID")
    base_url: Optional[str] = Field(
        default=None,
        description="Boomi API base URL (optional - SDK will use default if not provided)"
    )


# --- Tools ---
@mcp.tool()
def set_boomi_credentials(p: SetCreds) -> str:
    """
    Store Boomi credentials for a profile (requires 'secrets:write' scope).

    Credentials are stored securely per user and never logged or displayed.
    Use different profiles for different environments (e.g., 'sandbox', 'prod').
    """
    subject, scopes = get_user_info()
    require("secrets:write", scopes)

    put_secret(subject, p.profile, {
        "username": p.username,
        "password": p.password,
        "account_id": p.account_id,
        "base_url": p.base_url,
    })

    return f"✓ Stored credentials for profile '{p.profile}'"


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
def delete_boomi_profile(p: Profile):
    """
    Delete a Boomi profile (requires 'secrets:write' scope).

    This permanently removes stored credentials for the profile.
    """
    subject, scopes = get_user_info()
    require("secrets:write", scopes)

    try:
        delete_profile(subject, p.profile)
        return f"✓ Deleted profile '{p.profile}'"
    except ValueError as e:
        return f"✗ {str(e)}"


@mcp.tool()
def boomi_account_info(p: Profile):
    """
    Get Boomi account information (requires 'boomi:read' scope).

    Retrieves account details from Boomi API using stored credentials.
    This implements the core logic from boomi-python/examples/12_utilities/sample.py:
    1. Initialize Boomi SDK with stored credentials
    2. Call account.get_account() to retrieve account information
    3. Return structured account data
    """
    subject, scopes = get_user_info()
    require("boomi:read", scopes)

    # Get stored credentials
    try:
        creds = get_secret(subject, p.profile)
    except ValueError as e:
        return {"error": str(e), "success": False}

    print(f"[INFO] Calling Boomi API for {subject}:{p.profile} (account: {creds['account_id']})")

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
    print(f"JWT Algorithm: {JWT_ALG}")
    print(f"JWT Issuer:    {JWT_ISSUER}")
    print(f"JWT Audience:  {JWT_AUDIENCE}")
    print(f"Secrets DB:    {DB_PATH}")
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
