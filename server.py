#!/usr/bin/env python3
"""
Boomi MCP Server - FastMCP server with OAuth for Boomi API integration.

Security features:
- OAuth 2.0 authentication (Google)
- Per-user credential storage (GCP Secret Manager)
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
    print(f"       Run: pip install git+https://github.com/RenEra-ai/boomi-python.git")
    sys.exit(1)

# --- Cloud Secrets Manager (GCP/AWS/Azure) ---
try:
    from boomi_mcp.cloud_secrets import get_secrets_backend
    secrets_backend = get_secrets_backend()
    backend_type = os.getenv("SECRETS_BACKEND", "gcp")
    print(f"[INFO] Using secrets backend: {backend_type}")
    if backend_type == "gcp":
        project_id = os.getenv("GCP_PROJECT_ID", "boomimcp")
        print(f"[INFO] GCP Project: {project_id}")
except ImportError as e:
    print(f"ERROR: Failed to import cloud_secrets: {e}")
    print(f"       Make sure src/boomi_mcp/cloud_secrets.py exists")
    sys.exit(1)

# --- Trading Partner Tools ---
try:
    from boomi_mcp.categories.components.trading_partners import manage_trading_partner_action
    print(f"[INFO] Trading partner tools loaded successfully")
except ImportError as e:
    print(f"[WARNING] Failed to import trading partner tools: {e}")
    manage_trading_partner_action = None


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
from fastmcp.server.auth.providers.google import GoogleTokenVerifier
from fastmcp.server.auth.oauth_proxy import OAuthProxy

# Custom GoogleProvider with refresh token support
class GoogleProviderWithRefresh(OAuthProxy):
    """Google OAuth provider with refresh token support for long-lived sessions."""

    def __init__(self, client_id: str, client_secret: str, base_url: str):
        # Create Google token verifier
        token_verifier = GoogleTokenVerifier(
            required_scopes=["openid"],
            timeout_seconds=10,
        )

        # Initialize OAuth proxy with Google endpoints and refresh token support
        super().__init__(
            upstream_authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            upstream_token_endpoint="https://oauth2.googleapis.com/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            token_verifier=token_verifier,
            base_url=base_url,
            redirect_path="/auth/callback",
            issuer_url=base_url,
            allowed_client_redirect_uris=None,  # Allow all redirect URIs
            extra_authorize_params={
                "access_type": "offline",  # Request refresh token
                "prompt": "consent",  # Force consent to ensure refresh token
            },
        )

# Create Google OAuth provider
try:
    client_id = os.getenv("OIDC_CLIENT_ID")
    client_secret = os.getenv("OIDC_CLIENT_SECRET")
    base_url = os.getenv("OIDC_BASE_URL", "http://localhost:8000")

    if not client_id or not client_secret:
        raise ValueError("OIDC_CLIENT_ID and OIDC_CLIENT_SECRET must be set")

    auth = GoogleProviderWithRefresh(
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url,
    )

    print(f"[INFO] Google OAuth 2.0 configured with refresh token support")
    print(f"[INFO] Base URL: {base_url}")
    print(f"[INFO] All authenticated Google users have full access to all tools")
    print(f"[INFO] Sessions will be maintained automatically via refresh tokens")
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
# TODO: Add branding (icons, site) when FastMCP 2.14.0+ is released
mcp = FastMCP(
    name="Boomi MCP Server",
    auth=auth
)

# Add SessionMiddleware for web UI OAuth flow
# This is required for storing OAuth state and code_verifier between requests
session_secret = os.getenv("SESSION_SECRET")
if not session_secret:
    print("[ERROR] SESSION_SECRET environment variable must be set for web UI")
    sys.exit(1)

# Access the underlying Starlette app and add SessionMiddleware
if hasattr(mcp, '_app'):
    mcp._app.add_middleware(SessionMiddleware, secret_key=session_secret, max_age=3600)
    print(f"[INFO] SessionMiddleware configured for web UI")
elif hasattr(mcp, 'app'):
    mcp.app.add_middleware(SessionMiddleware, secret_key=session_secret, max_age=3600)
    print(f"[INFO] SessionMiddleware configured for web UI")


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

@mcp.tool()
def list_boomi_profiles():
    """
    List all saved Boomi credential profiles for the authenticated user.

    Returns a list of profile names that can be used with boomi_account_info().
    Use this tool first to see which profiles are available before requesting account info.

    Returns:
        List of profile objects with 'profile' name and metadata
    """
    try:
        subject = get_user_subject()
        print(f"[INFO] list_boomi_profiles called by user: {subject}")

        profiles = list_profiles(subject)
        print(f"[INFO] Found {len(profiles)} profiles for {subject}")

        if not profiles:
            return {
                "_success": True,
                "profiles": [],
                "message": "No profiles found. Add credentials at https://boomi.renera.ai/",
                "web_portal": "https://boomi.renera.ai/"
            }

        return {
            "_success": True,
            "profiles": [p["profile"] for p in profiles],
            "count": len(profiles),
            "web_portal": "https://boomi.renera.ai/"
        }
    except Exception as e:
        print(f"[ERROR] Failed to list profiles: {e}")
        return {
            "_success": False,
            "error": f"Failed to list profiles: {str(e)}",
            "_note": "Make sure you're authenticated with OAuth"
        }

# @mcp.tool()
# def delete_boomi_profile(...):
#     """Use the web UI to delete profiles"""
#     pass


@mcp.tool()
def boomi_account_info(profile: str):
    """
    Get Boomi account information from a specific profile.

    MULTI-ACCOUNT SUPPORT:
    - Users can store multiple Boomi accounts (up to 10 profiles)
    - Each profile has a unique name (e.g., 'production', 'sandbox', 'dev')
    - Profile name is REQUIRED - there is no default profile
    - If user has multiple profiles, ASK which one to use for the task
    - Once user specifies a profile, continue using it for subsequent calls
    - Don't repeatedly ask if already working with a selected profile

    WORKFLOW:
    1. First call: Use list_boomi_profiles to see available profiles
    2. If multiple profiles exist, ask user which one to use
    3. If only one profile exists, use that one
    4. Use the selected profile for all subsequent Boomi API calls in this conversation
    5. Only ask again if user explicitly wants to switch accounts

    WEB PORTAL:
    - Store credentials at: https://boomi.renera.ai/
    - Each credential set is stored as a named profile
    - Profile name is required when adding credentials
    - Users can add, delete, and switch between profiles

    Args:
        profile: Profile name to use (REQUIRED - no default)

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


# --- Trading Partner MCP Tools ---
if manage_trading_partner_action:
    @mcp.tool()
    def manage_trading_partner(
        profile: str,
        action: str,
        partner_id: str = None,
        component_name: str = None,
        standard: str = None,
        classification: str = None,
        folder_name: str = None,
        # X12 standard fields
        isa_id: str = None,
        isa_qualifier: str = None,
        gs_id: str = None,
        # Contact Information
        contact_name: str = None,
        contact_email: str = None,
        contact_phone: str = None,
        contact_fax: str = None,
        contact_address: str = None,
        contact_address2: str = None,
        contact_city: str = None,
        contact_state: str = None,
        contact_country: str = None,
        contact_postalcode: str = None,
        # Communication Protocols
        communication_protocols: str = None,
        # Disk protocol fields
        disk_get_directory: str = None,
        disk_send_directory: str = None,
        # FTP protocol fields
        ftp_host: str = None,
        ftp_port: str = None,
        ftp_username: str = None,
        ftp_password: str = None,
        ftp_remote_directory: str = None,
        # SFTP protocol fields
        sftp_host: str = None,
        sftp_port: str = None,
        sftp_username: str = None,
        sftp_password: str = None,
        sftp_remote_directory: str = None,
        # HTTP protocol fields
        http_url: str = None,
        http_username: str = None,
        http_password: str = None,
        http_authentication_type: str = None,
        # AS2 protocol fields
        as2_url: str = None,
        as2_identifier: str = None,
        as2_partner_identifier: str = None,
        as2_username: str = None,
        as2_password: str = None
    ):
        """
        Manage B2B/EDI trading partners with communication protocols.

        IMPORTANT: Before calling this tool, ask the user to choose:

        1. TRADING STANDARD: x12, edifact, hl7, rosettanet, custom, tradacoms, odette
        2. CLASSIFICATION: "tradingpartner" or "mytradingpartner" (my company)
        3. COMMUNICATION PROTOCOL: disk, ftp, sftp, http, as2 (comma-separated for multiple)

        Args:
            profile: Boomi profile name (required)
            action: list, get, create, update, delete, analyze_usage
            partner_id: Component ID (required for get/update/delete)
            component_name: Partner name (required for create)
            standard: x12, edifact, hl7, rosettanet, custom, tradacoms, odette
            classification: tradingpartner or mytradingpartner
            folder_name: Folder location

            # X12 Fields
            isa_id, isa_qualifier, gs_id: X12 identifiers

            # Contact Info
            contact_name, contact_email, contact_phone, contact_fax
            contact_address, contact_address2, contact_city, contact_state, contact_country, contact_postalcode

            # Communication Protocols
            communication_protocols: Comma-separated list (e.g., "ftp,http")

            # Disk: disk_get_directory, disk_send_directory
            # FTP: ftp_host, ftp_port, ftp_username, ftp_password, ftp_remote_directory
            # SFTP: sftp_host, sftp_port, sftp_username, sftp_password, sftp_remote_directory
            # HTTP: http_url, http_username, http_password, http_authentication_type
            # AS2: as2_url, as2_identifier, as2_partner_identifier, as2_username, as2_password

        Returns:
            Action result with success status and data/error
        """
        try:
            subject = get_user_subject()
            print(f"[INFO] manage_trading_partner called by user: {subject}, profile: {profile}, action: {action}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            # Build parameters based on action
            params = {}

            if action == "list":
                # Build filters
                filters = {}
                if standard:
                    filters["standard"] = standard
                if classification:
                    filters["classification"] = classification
                if folder_name:
                    filters["folder_name"] = folder_name
                params["filters"] = filters

            elif action == "get":
                params["partner_id"] = partner_id

            elif action == "create":
                # Build request data with flat parameters
                request_data = {}
                if component_name:
                    request_data["component_name"] = component_name
                if standard:
                    request_data["standard"] = standard
                if classification:
                    request_data["classification"] = classification
                if folder_name:
                    request_data["folder_name"] = folder_name

                # X12 fields (flat)
                if isa_id:
                    request_data["isa_id"] = isa_id
                if isa_qualifier:
                    request_data["isa_qualifier"] = isa_qualifier
                if gs_id:
                    request_data["gs_id"] = gs_id

                # Contact info (flat)
                if contact_name:
                    request_data["contact_name"] = contact_name
                if contact_email:
                    request_data["contact_email"] = contact_email
                if contact_phone:
                    request_data["contact_phone"] = contact_phone
                if contact_fax:
                    request_data["contact_fax"] = contact_fax
                if contact_address:
                    request_data["contact_address"] = contact_address
                if contact_address2:
                    request_data["contact_address2"] = contact_address2
                if contact_city:
                    request_data["contact_city"] = contact_city
                if contact_state:
                    request_data["contact_state"] = contact_state
                if contact_country:
                    request_data["contact_country"] = contact_country
                if contact_postalcode:
                    request_data["contact_postalcode"] = contact_postalcode

                # Communication protocols
                if communication_protocols:
                    protocols_list = [p.strip() for p in communication_protocols.split(',')]
                    request_data["communication_protocols"] = protocols_list

                # Disk protocol fields
                if disk_get_directory:
                    request_data["disk_get_directory"] = disk_get_directory
                if disk_send_directory:
                    request_data["disk_send_directory"] = disk_send_directory

                # FTP protocol fields
                if ftp_host:
                    request_data["ftp_host"] = ftp_host
                if ftp_port:
                    request_data["ftp_port"] = ftp_port
                if ftp_username:
                    request_data["ftp_username"] = ftp_username
                if ftp_password:
                    request_data["ftp_password"] = ftp_password
                if ftp_remote_directory:
                    request_data["ftp_remote_directory"] = ftp_remote_directory

                # SFTP protocol fields
                if sftp_host:
                    request_data["sftp_host"] = sftp_host
                if sftp_port:
                    request_data["sftp_port"] = sftp_port
                if sftp_username:
                    request_data["sftp_username"] = sftp_username
                if sftp_password:
                    request_data["sftp_password"] = sftp_password
                if sftp_remote_directory:
                    request_data["sftp_remote_directory"] = sftp_remote_directory

                # HTTP protocol fields
                if http_url:
                    request_data["http_url"] = http_url
                if http_username:
                    request_data["http_username"] = http_username
                if http_password:
                    request_data["http_password"] = http_password
                if http_authentication_type:
                    request_data["http_authentication_type"] = http_authentication_type

                # AS2 protocol fields
                if as2_url:
                    request_data["as2_url"] = as2_url
                if as2_identifier:
                    request_data["as2_identifier"] = as2_identifier
                if as2_partner_identifier:
                    request_data["as2_partner_identifier"] = as2_partner_identifier
                if as2_username:
                    request_data["as2_username"] = as2_username
                if as2_password:
                    request_data["as2_password"] = as2_password

                params["request_data"] = request_data

            elif action == "update":
                params["partner_id"] = partner_id

                # Build updates with flat parameters
                updates = {}
                if component_name:
                    updates["component_name"] = component_name

                # X12 fields
                if isa_id:
                    updates["isa_id"] = isa_id
                if isa_qualifier:
                    updates["isa_qualifier"] = isa_qualifier
                if gs_id:
                    updates["gs_id"] = gs_id

                # Contact info (flat)
                if contact_name:
                    updates["contact_name"] = contact_name
                if contact_email:
                    updates["contact_email"] = contact_email
                if contact_phone:
                    updates["contact_phone"] = contact_phone
                if contact_fax:
                    updates["contact_fax"] = contact_fax
                if contact_address:
                    updates["contact_address"] = contact_address
                if contact_address2:
                    updates["contact_address2"] = contact_address2
                if contact_city:
                    updates["contact_city"] = contact_city
                if contact_state:
                    updates["contact_state"] = contact_state
                if contact_country:
                    updates["contact_country"] = contact_country
                if contact_postalcode:
                    updates["contact_postalcode"] = contact_postalcode

                # Communication protocols
                if communication_protocols:
                    protocols_list = [p.strip() for p in communication_protocols.split(',')]
                    updates["communication_protocols"] = protocols_list

                # Disk protocol fields
                if disk_get_directory:
                    updates["disk_get_directory"] = disk_get_directory
                if disk_send_directory:
                    updates["disk_send_directory"] = disk_send_directory

                # FTP protocol fields
                if ftp_host:
                    updates["ftp_host"] = ftp_host
                if ftp_port:
                    updates["ftp_port"] = ftp_port
                if ftp_username:
                    updates["ftp_username"] = ftp_username
                if ftp_password:
                    updates["ftp_password"] = ftp_password
                if ftp_remote_directory:
                    updates["ftp_remote_directory"] = ftp_remote_directory

                # SFTP protocol fields
                if sftp_host:
                    updates["sftp_host"] = sftp_host
                if sftp_port:
                    updates["sftp_port"] = sftp_port
                if sftp_username:
                    updates["sftp_username"] = sftp_username
                if sftp_password:
                    updates["sftp_password"] = sftp_password
                if sftp_remote_directory:
                    updates["sftp_remote_directory"] = sftp_remote_directory

                # HTTP protocol fields
                if http_url:
                    updates["http_url"] = http_url
                if http_username:
                    updates["http_username"] = http_username
                if http_password:
                    updates["http_password"] = http_password
                if http_authentication_type:
                    updates["http_authentication_type"] = http_authentication_type

                # AS2 protocol fields
                if as2_url:
                    updates["as2_url"] = as2_url
                if as2_identifier:
                    updates["as2_identifier"] = as2_identifier
                if as2_partner_identifier:
                    updates["as2_partner_identifier"] = as2_partner_identifier
                if as2_username:
                    updates["as2_username"] = as2_username
                if as2_password:
                    updates["as2_password"] = as2_password

                params["updates"] = updates

            elif action == "delete":
                params["partner_id"] = partner_id

            elif action == "analyze_usage":
                params["partner_id"] = partner_id

            # Route to appropriate function
            return manage_trading_partner_action(sdk, profile, action, **params)

        except Exception as e:
            print(f"[ERROR] Failed to {action} trading partner: {e}")
            return {"_success": False, "error": str(e)}

    print("[INFO] Trading partner tool registered successfully (1 consolidated tool)")


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

    print(f"[DEBUG] Stored in session: oauth_state={state[:20]}..., code_verifier={code_verifier[:20]}...")
    print(f"[DEBUG] Session after store: {dict(request.session)}")

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

    print(f"[DEBUG] Callback received - state from URL: {state[:20] if state else 'None'}...")
    print(f"[DEBUG] Session contents: {dict(request.session)}")
    print(f"[DEBUG] Session ID: {id(request.session)}")
    print(f"[DEBUG] Has session attr: {hasattr(request, 'session')}")

    if error:
        return HTMLResponse(f"<html><body><h1>OAuth Error</h1><p>{error}</p></body></html>", status_code=400)

    if not code or not state:
        return HTMLResponse("<html><body><h1>OAuth Error</h1><p>Missing code or state</p></body></html>", status_code=400)

    # Verify state
    stored_state = request.session.get("oauth_state")
    print(f"[DEBUG] Stored state from session: {stored_state[:20] if stored_state else 'None'}...")
    print(f"[DEBUG] State match: {state == stored_state}")

    if not stored_state or state != stored_state:
        return HTMLResponse(
            f"<html><body><h1>OAuth Error</h1>"
            f"<p>Invalid state</p>"
            f"<p>Debug: Expected state in session but got empty session</p>"
            f"<p>Session keys: {list(request.session.keys())}</p>"
            f"</body></html>",
            status_code=400
        )

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

    # Get server URL from environment or request
    base_url = os.getenv("OIDC_BASE_URL")
    if not base_url:
        # Fallback to request base URL
        base_url = str(request.base_url).rstrip('/')

    server_url = f"{base_url}/mcp"

    # Replace template variables
    html = html.replace("{{ user_email }}", subject)
    html = html.replace("{{ server_url }}", server_url)

    return HTMLResponse(html)


@mcp.custom_route("/api/credentials/validate", methods=["POST"])
async def api_validate_credentials(request: Request):
    """API endpoint to validate Boomi credentials before saving."""
    subject = get_authenticated_user(request)
    if not subject:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        data = await request.json()

        print(f"[DEBUG] Validating credentials for account_id: {data['account_id']}, username: {data['username'][:30]}...")

        # Test credentials by attempting to initialize Boomi SDK and make a simple API call
        # Don't pass base_url - let SDK use default which auto-formats {accountId}
        test_sdk = Boomi(
            account_id=data["account_id"],
            username=data["username"],
            password=data["password"],
            timeout=10000,
        )

        # Try to get account info - this will fail if credentials are invalid
        print(f"[DEBUG] Calling Boomi API: account.get_account(id_={data['account_id']})")
        result = test_sdk.account.get_account(id_=data["account_id"])

        if result:
            print(f"[DEBUG] Validation successful for {data['account_id']}")
            return JSONResponse({
                "success": True,
                "message": "Credentials validated successfully"
            })
        else:
            print(f"[ERROR] Validation returned no result for {data['account_id']}")
            return JSONResponse({"error": "Failed to validate credentials"}, status_code=400)

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Validation exception: {error_msg}")
        print(f"[ERROR] Exception type: {type(e).__name__}")

        # Provide user-friendly error messages
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "Invalid username or password"
        elif "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "Access denied - check your account permissions"
        elif "404" in error_msg or "Not Found" in error_msg:
            error_msg = "Account ID not found"
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout - please try again"

        return JSONResponse({"error": f"Validation failed: {error_msg}"}, status_code=400)


@mcp.custom_route("/api/credentials", methods=["POST"])
async def api_set_credentials(request: Request):
    """API endpoint to save credentials."""
    subject = get_authenticated_user(request)
    if not subject:
        return JSONResponse({"error": "Authentication required"}, status_code=401)

    try:
        data = await request.json()

        # Check profile limit (10 profiles per user)
        existing_profiles = list_profiles(subject)
        profile_name = data["profile"]

        # Allow updating existing profile, but limit new profiles to 10
        is_new_profile = profile_name not in [p["profile"] for p in existing_profiles]
        if is_new_profile and len(existing_profiles) >= 10:
            return JSONResponse({
                "error": "Profile limit reached. You can store up to 10 Boomi account profiles. Please delete an existing profile before adding a new one."
            }, status_code=400)

        # Don't store base_url - let SDK use default which auto-formats {accountId}
        put_secret(subject, profile_name, {
            "username": data["username"],
            "password": data["password"],
            "account_id": data["account_id"],
        })

        return JSONResponse({
            "success": True,
            "message": f"Credentials saved for profile '{profile_name}'"
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

    provider_type = os.getenv("OIDC_PROVIDER", "google")
    base_url = os.getenv("OIDC_BASE_URL", "http://localhost:8000")
    backend_type = os.getenv("SECRETS_BACKEND", "gcp")
    print(f"Auth Mode:     OAuth 2.0 ({provider_type})")
    print(f"Base URL:      {base_url}")
    print(f"Login URL:     {base_url}/auth/login")
    print(f"Secrets:       {backend_type.upper()}")
    if backend_type == "gcp":
        print(f"GCP Project:   {os.getenv('GCP_PROJECT_ID', 'boomimcp')}")
    print("=" * 60)

    print("=" * 60)
    print("\n🌐 Web Interface:")
    print(f"  Credential Management: {base_url}/")
    print("  (Login with Google to store your Boomi credentials)")
    print("\n🔧 MCP Tools available:")
    print("  • boomi_account_info - Get account information from Boomi API")
    if trading_partner_tools:
        print("\n  🤝 Trading Partner Management:")
        print("  • list_trading_partners - List all trading partners with filtering")
        print("  • get_trading_partner - Get specific trading partner details")
        print("  • create_trading_partner - Create new trading partners (X12, EDIFACT, HL7, etc.)")
        print("  • update_trading_partner - Update trading partner information")
        print("  • delete_trading_partner - Delete a trading partner")
        print("  • analyze_trading_partner_usage - Analyze partner usage in processes")
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
