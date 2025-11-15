#!/usr/bin/env python3
"""
Boomi MCP Server - LOCAL DEVELOPMENT VERSION

This is a simplified version for local testing without OAuth or Docker.
Use this for fast iteration when developing new MCP tools.

Features:
- No OAuth authentication (for local testing only)
- Local file-based credential storage (~/.boomi_mcp_local_secrets.json)
- No Docker build required
- Fast startup for rapid development

NOT FOR PRODUCTION USE - Use server.py with OAuth for production.
"""

import os
import sys
from typing import Dict
from pathlib import Path

from fastmcp import FastMCP

# --- Add boomi-python to path ---
boomi_python_path = Path(__file__).parent.parent / "boomi-python"
if boomi_python_path.exists():
    sys.path.insert(0, str(boomi_python_path))

# --- Add src to path for local_secrets ---
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

# --- Local Secrets Storage ---
try:
    from boomi_mcp.local_secrets import LocalSecretsBackend
    secrets_backend = LocalSecretsBackend()
    print(f"[INFO] Using local file-based secrets storage")
    print(f"[INFO] Storage file: {secrets_backend.storage_file}")
except ImportError as e:
    print(f"ERROR: Failed to import local_secrets: {e}")
    print(f"       Make sure src/boomi_mcp/local_secrets.py exists")
    sys.exit(1)

# --- Trading Partner Tools ---
try:
    from boomi_mcp.categories.components.trading_partners import manage_trading_partner_action
    print(f"[INFO] Trading partner tools loaded successfully")
except ImportError as e:
    print(f"[WARNING] Failed to import trading_partner_tools: {e}")
    manage_trading_partner_action = None


def put_secret(subject: str, profile: str, payload: Dict[str, str]):
    """Store credentials for a user profile."""
    secrets_backend.put_secret(subject, profile, payload)
    print(f"[INFO] Stored credentials for {subject}:{profile} (username: {payload.get('username', '')[:10]}***)")


def get_secret(subject: str, profile: str) -> Dict[str, str]:
    """Retrieve credentials for a user profile."""
    return secrets_backend.get_secret(subject, profile)


def list_profiles(subject: str):
    """List all profiles for a user."""
    return secrets_backend.list_profiles(subject)


def delete_profile(subject: str, profile: str):
    """Delete a user profile."""
    secrets_backend.delete_profile(subject, profile)


# --- Create FastMCP server WITHOUT authentication (local dev only) ---
mcp = FastMCP(
    name="Boomi MCP Server (Local Dev)"
)

# Hardcoded test user for local development
# In production, this comes from OAuth
TEST_USER = "local-dev-user"


# --- Tools ---

@mcp.tool()
def list_boomi_profiles():
    """
    List all saved Boomi credential profiles for the local test user.

    Returns a list of profile names that can be used with boomi_account_info().
    Use this tool first to see which profiles are available before requesting account info.

    Returns:
        List of profile objects with 'profile' name and metadata
    """
    try:
        subject = TEST_USER
        print(f"[INFO] list_boomi_profiles called for local user: {subject}")

        profiles = list_profiles(subject)
        print(f"[INFO] Found {len(profiles)} profiles for {subject}")

        if not profiles:
            return {
                "_success": True,
                "profiles": [],
                "message": "No profiles found. Use set_boomi_credentials tool to add credentials.",
                "_note": "This is the local development version"
            }

        return {
            "_success": True,
            "profiles": [p["profile"] for p in profiles],
            "count": len(profiles),
            "_note": "This is the local development version"
        }
    except Exception as e:
        print(f"[ERROR] Failed to list profiles: {e}")
        return {
            "_success": False,
            "error": f"Failed to list profiles: {str(e)}"
        }


@mcp.tool()
def set_boomi_credentials(
    profile: str,
    account_id: str,
    username: str,
    password: str
):
    """
    Store Boomi API credentials for local testing.

    This tool is only available in the local development version.
    In production, credentials are managed via the web UI.

    Args:
        profile: Profile name (e.g., 'production', 'sandbox', 'dev')
        account_id: Boomi account ID
        username: Boomi API username (should start with BOOMI_TOKEN.)
        password: Boomi API password/token

    Returns:
        Success confirmation or error details
    """
    try:
        subject = TEST_USER
        print(f"[INFO] set_boomi_credentials called for profile: {profile}")

        # Validate credentials by making a test API call
        try:
            test_sdk = Boomi(
                account_id=account_id,
                username=username,
                password=password,
                timeout=10000,
            )
            test_sdk.account.get_account(id_=account_id)
            print(f"[INFO] Credentials validated successfully for {account_id}")
        except Exception as e:
            print(f"[ERROR] Credential validation failed: {e}")
            return {
                "_success": False,
                "error": f"Credential validation failed: {str(e)}",
                "_note": "Please check your account_id, username, and password"
            }

        # Store credentials
        put_secret(subject, profile, {
            "username": username,
            "password": password,
            "account_id": account_id,
        })

        return {
            "_success": True,
            "message": f"Credentials saved for profile '{profile}'",
            "profile": profile,
            "_note": "Credentials stored locally in ~/.boomi_mcp_local_secrets.json"
        }
    except Exception as e:
        print(f"[ERROR] Failed to set credentials: {e}")
        return {
            "_success": False,
            "error": str(e)
        }


@mcp.tool()
def delete_boomi_profile(profile: str):
    """
    Delete a stored Boomi credential profile.

    This tool is only available in the local development version.
    In production, profiles are managed via the web UI.

    Args:
        profile: Profile name to delete

    Returns:
        Success confirmation or error details
    """
    try:
        subject = TEST_USER
        print(f"[INFO] delete_boomi_profile called for profile: {profile}")

        delete_profile(subject, profile)

        return {
            "_success": True,
            "message": f"Profile '{profile}' deleted successfully",
            "_note": "This is the local development version"
        }
    except Exception as e:
        print(f"[ERROR] Failed to delete profile: {e}")
        return {
            "_success": False,
            "error": str(e)
        }


@mcp.tool()
def boomi_account_info(profile: str):
    """
    Get Boomi account information from a specific profile.

    MULTI-ACCOUNT SUPPORT:
    - Users can store multiple Boomi accounts (unlimited in local dev)
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

    LOCAL DEV VERSION:
    - Store credentials using set_boomi_credentials tool
    - No web UI available in local dev mode
    - Credentials stored in ~/.boomi_mcp_local_secrets.json

    Args:
        profile: Profile name to use (REQUIRED - no default)

    Returns:
        Account information including name, status, licensing details, or error details
    """
    try:
        subject = TEST_USER
        print(f"[INFO] boomi_account_info called for profile: {profile}")
    except Exception as e:
        print(f"[ERROR] Failed to get user subject: {e}")
        return {
            "_success": False,
            "error": f"Failed: {str(e)}"
        }

    # Try to get stored credentials
    try:
        creds = get_secret(subject, profile)
        print(f"[INFO] Successfully retrieved stored credentials for profile: {profile}")
        print(f"[INFO] Account ID: {creds.get('account_id')}, Username: {creds.get('username', '')[:20]}...")
    except ValueError as e:
        print(f"[ERROR] Profile '{profile}' not found: {e}")

        # List available profiles
        available_profiles = list_profiles(subject)
        print(f"[INFO] Available profiles: {[p['profile'] for p in available_profiles]}")

        return {
            "_success": False,
            "error": f"Profile '{profile}' not found. Use set_boomi_credentials to add credentials.",
            "available_profiles": [p["profile"] for p in available_profiles],
            "_note": "Use set_boomi_credentials tool to store credentials for this profile"
        }
    except Exception as e:
        print(f"[ERROR] Unexpected error retrieving credentials: {e}")
        return {
            "_success": False,
            "error": f"Failed to retrieve credentials: {str(e)}"
        }

    print(f"[INFO] Calling Boomi API for profile: {profile} (account: {creds['account_id']})")

    # Initialize Boomi SDK
    try:
        sdk_params = {
            "account_id": creds["account_id"],
            "username": creds["username"],
            "password": creds["password"],
            "timeout": 30000,  # 30 seconds
        }

        # Only add base_url if explicitly provided
        if creds.get("base_url"):
            sdk_params["base_url"] = creds["base_url"]

        sdk = Boomi(**sdk_params)

        # Call API
        result = sdk.account.get_account(id_=creds["account_id"])

        # Convert to plain dict for transport
        if hasattr(result, "__dict__"):
            out = {
                k: v for k, v in result.__dict__.items()
                if not k.startswith("_") and v is not None
            }
            out["_success"] = True
            out["_note"] = "Account data retrieved successfully (local dev version)"
            print(f"[INFO] Successfully retrieved account info for {creds['account_id']}")
            return out

        return {
            "_success": True,
            "message": "Account object created; minimal data returned.",
            "_note": "This indicates successful authentication (local dev version)."
        }

    except Exception as e:
        print(f"[ERROR] Boomi API call failed: {e}")
        return {
            "_success": False,
            "error": str(e),
            "account_id": creds["account_id"],
            "_note": "Check credentials and API access permissions"
        }


# --- Trading Partner MCP Tools (Local) ---
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
        isa_id: str = None,
        isa_qualifier: str = None,
        gs_id: str = None,
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
        communication_protocols: str = None,
        disk_directory: str = None,
        disk_get_directory: str = None,
        disk_send_directory: str = None,
        ftp_host: str = None,
        ftp_port: str = None,
        ftp_username: str = None,
        sftp_host: str = None,
        sftp_port: str = None,
        sftp_username: str = None,
        http_url: str = None,
        as2_url: str = None,
        as2_identifier: str = None,
        as2_partner_identifier: str = None
    ):
        """
        Manage B2B/EDI trading partners (all 7 standards).

        Consolidated tool for all trading partner operations (local dev mode).

        Args:
            profile: Boomi profile name (required)
            action: Action to perform - must be one of: list, get, create, update, delete, analyze_usage
            partner_id: Trading partner component ID (required for get, update, delete, analyze_usage)
            component_name: Trading partner name (required for create, optional for update)
            standard: Trading standard (required for create, optional filter for list)
            classification: Partner classification (optional for create/list)
            folder_name: Folder to place partner in (optional for create/list)
            isa_id: ISA ID for X12 partners (X12 only)
            isa_qualifier: ISA Qualifier for X12 partners (X12 only)
            gs_id: GS ID for X12 partners (X12 only)
            contact_name: Contact person name (optional)
            contact_email: Contact email address (optional)
            contact_phone: Contact phone number (optional)
            contact_fax: Contact fax number (optional)
            contact_address: Contact street address line 1 (optional)
            contact_address2: Contact street address line 2 (optional)
            contact_city: Contact city (optional)
            contact_state: Contact state/province (optional)
            contact_country: Contact country (optional)
            contact_postalcode: Contact postal/zip code (optional)
            communication_protocols: Comma-separated list of communication protocols to enable (optional for create)
                                    Available: ftp, sftp, http, as2, mllp, oftp, disk
                                    Example: "ftp,http" or "as2,sftp"
                                    If not provided, creates partner with no communication configured (can be added later via UI)
            disk_directory: Main directory for Disk protocol (DiskSettings/@directory)
            disk_get_directory: Get/Receive directory for Disk protocol (DiskGetAction/@getDirectory)
            disk_send_directory: Send directory for Disk protocol (DiskSendAction/@sendDirectory)
            ftp_host: FTP server hostname/IP (ConnectionSettings/@host)
            ftp_port: FTP server port (ConnectionSettings/@port)
            ftp_username: FTP username (AuthSettings/@username)
            sftp_host: SFTP server hostname/IP (ConnectionSettings/@host)
            sftp_port: SFTP server port (ConnectionSettings/@port)
            sftp_username: SFTP username (AuthSettings/@username)
            http_url: HTTP/HTTPS URL (HTTPSettings/@url)
            as2_url: AS2 endpoint URL (AS2Settings/@url)
            as2_identifier: Local AS2 identifier (AS2Settings/@as2Identifier)
            as2_partner_identifier: Partner AS2 identifier (AS2Settings/@partnerAS2Identifier)

        Returns:
            Action result with success status and data/error
        """
        try:
            subject = TEST_USER
            print(f"[INFO] manage_trading_partner called for local user: {subject}, profile: {profile}, action: {action}")

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
                request_data = {}
                if component_name:
                    request_data["component_name"] = component_name
                if standard:
                    request_data["standard"] = standard
                if classification:
                    request_data["classification"] = classification
                if folder_name:
                    request_data["folder_name"] = folder_name

                if standard and standard.lower() == "x12" and (isa_id or isa_qualifier or gs_id):
                    request_data["partner_info"] = {}
                    if isa_id:
                        request_data["partner_info"]["isa_id"] = isa_id
                    if isa_qualifier:
                        request_data["partner_info"]["isa_qualifier"] = isa_qualifier
                    if gs_id:
                        request_data["partner_info"]["gs_id"] = gs_id

                if contact_name or contact_email or contact_phone or contact_fax or contact_address or contact_address2 or contact_city or contact_state or contact_country or contact_postalcode:
                    request_data["contact_info"] = {}
                    if contact_name:
                        request_data["contact_info"]["name"] = contact_name
                    if contact_email:
                        request_data["contact_info"]["email"] = contact_email
                    if contact_phone:
                        request_data["contact_info"]["phone"] = contact_phone
                    if contact_fax:
                        request_data["contact_info"]["fax"] = contact_fax
                    if contact_address:
                        request_data["contact_info"]["address"] = contact_address
                    if contact_address2:
                        request_data["contact_info"]["address2"] = contact_address2
                    if contact_city:
                        request_data["contact_info"]["city"] = contact_city
                    if contact_state:
                        request_data["contact_info"]["state"] = contact_state
                    if contact_country:
                        request_data["contact_info"]["country"] = contact_country
                    if contact_postalcode:
                        request_data["contact_info"]["postal_code"] = contact_postalcode

                # Add communication protocols if provided
                if communication_protocols:
                    protocols_list = [p.strip() for p in communication_protocols.split(',')]
                    request_data["communication_protocols"] = protocols_list

                params["request_data"] = request_data

            elif action == "update":
                params["partner_id"] = partner_id
                updates = {}
                if component_name:
                    updates["component_name"] = component_name

                if contact_name or contact_email or contact_phone or contact_fax or contact_address or contact_address2 or contact_city or contact_state or contact_country or contact_postalcode:
                    updates["contact_info"] = {}
                    if contact_name:
                        updates["contact_info"]["name"] = contact_name
                    if contact_email:
                        updates["contact_info"]["email"] = contact_email
                    if contact_phone:
                        updates["contact_info"]["phone"] = contact_phone
                    if contact_fax:
                        updates["contact_info"]["fax"] = contact_fax
                    if contact_address:
                        updates["contact_info"]["address"] = contact_address
                    if contact_address2:
                        updates["contact_info"]["address2"] = contact_address2
                    if contact_city:
                        updates["contact_info"]["city"] = contact_city
                    if contact_state:
                        updates["contact_info"]["state"] = contact_state
                    if contact_country:
                        updates["contact_info"]["country"] = contact_country
                    if contact_postalcode:
                        updates["contact_info"]["postal_code"] = contact_postalcode

                if isa_id or isa_qualifier or gs_id:
                    updates["partner_info"] = {}
                    if isa_id:
                        updates["partner_info"]["isa_id"] = isa_id
                    if isa_qualifier:
                        updates["partner_info"]["isa_qualifier"] = isa_qualifier
                    if gs_id:
                        updates["partner_info"]["gs_id"] = gs_id

                # Add communication protocols if provided
                if communication_protocols:
                    protocols_list = [p.strip() for p in communication_protocols.split(',')]
                    updates["communication_protocols"] = protocols_list

                # Add Disk communication directories if provided
                if disk_directory is not None or disk_get_directory is not None or disk_send_directory is not None:
                    updates["disk_settings"] = {}
                    if disk_directory is not None:
                        updates["disk_settings"]["directory"] = disk_directory
                    if disk_get_directory is not None:
                        updates["disk_settings"]["get_directory"] = disk_get_directory
                    if disk_send_directory is not None:
                        updates["disk_settings"]["send_directory"] = disk_send_directory

                # Add FTP settings if provided
                if ftp_host is not None or ftp_port is not None or ftp_username is not None:
                    updates["ftp_settings"] = {}
                    if ftp_host is not None:
                        updates["ftp_settings"]["host"] = ftp_host
                    if ftp_port is not None:
                        updates["ftp_settings"]["port"] = ftp_port
                    if ftp_username is not None:
                        updates["ftp_settings"]["username"] = ftp_username

                # Add SFTP settings if provided
                if sftp_host is not None or sftp_port is not None or sftp_username is not None:
                    updates["sftp_settings"] = {}
                    if sftp_host is not None:
                        updates["sftp_settings"]["host"] = sftp_host
                    if sftp_port is not None:
                        updates["sftp_settings"]["port"] = sftp_port
                    if sftp_username is not None:
                        updates["sftp_settings"]["username"] = sftp_username

                # Add HTTP settings if provided
                if http_url is not None:
                    updates["http_settings"] = {}
                    updates["http_settings"]["url"] = http_url

                # Add AS2 settings if provided
                if as2_url is not None or as2_identifier is not None or as2_partner_identifier is not None:
                    updates["as2_settings"] = {}
                    if as2_url is not None:
                        updates["as2_settings"]["url"] = as2_url
                    if as2_identifier is not None:
                        updates["as2_settings"]["as2_identifier"] = as2_identifier
                    if as2_partner_identifier is not None:
                        updates["as2_settings"]["partner_as2_identifier"] = as2_partner_identifier

                params["updates"] = updates

            elif action == "delete":
                params["partner_id"] = partner_id

            elif action == "analyze_usage":
                params["partner_id"] = partner_id

            return manage_trading_partner_action(sdk, profile, action, **params)

        except Exception as e:
            print(f"[ERROR] Failed to {action} trading partner: {e}")
            return {"_success": False, "error": str(e)}

    print("[INFO] Trading partner tool registered successfully (1 consolidated tool, local)")



if __name__ == "__main__":
    # Print startup info
    print("\n" + "=" * 60)
    print("🚀 Boomi MCP Server - LOCAL DEVELOPMENT MODE")
    print("=" * 60)
    print("⚠️  WARNING: This is for LOCAL TESTING ONLY")
    print("⚠️  No OAuth authentication - DO NOT use in production")
    print("=" * 60)
    print(f"Auth Mode:     None (local dev)")
    print(f"Storage:       Local file (~/.boomi_mcp_local_secrets.json)")
    print(f"Test User:     {TEST_USER}")
    print("=" * 60)
    print("\n🔧 MCP Tools available:")
    print("  • list_boomi_profiles - List saved credential profiles")
    print("  • set_boomi_credentials - Store Boomi credentials")
    print("  • delete_boomi_profile - Delete a credential profile")
    print("  • boomi_account_info - Get account information from Boomi API")
    if manage_trading_partner_action:
        print("\n  🤝 Trading Partner Management (CONSOLIDATED):")
        print("  • manage_trading_partner - Unified tool for all trading partner operations")
        print("    Actions: list, get, create, update, delete, analyze_usage")
        print("    Standards: X12, EDIFACT, HL7, RosettaNet, Custom, Tradacoms, Odette")
    print("\n📝 Quick Start:")
    print("  1. Connect with: claude mcp add boomi-local stdio -- python server_local.py")
    print("  2. Use set_boomi_credentials to store your Boomi API credentials")
    print("  3. Use boomi_account_info to test API calls")
    print("=" * 60 + "\n")

    # Run in stdio mode for fast local testing
    mcp.run(transport="stdio")
