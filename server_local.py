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
    from boomi_mcp import trading_partner_tools
    print(f"[INFO] Trading partner tools loaded successfully")
except ImportError as e:
    print(f"[WARNING] Failed to import trading_partner_tools: {e}")
    trading_partner_tools = None


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
if trading_partner_tools:
    @mcp.tool()
    def list_trading_partners(profile: str, standard: str = None, classification: str = None, folder_name: str = None):
        """
        List all trading partners with optional filtering.

        Args:
            profile: Boomi profile name (required)
            standard: Filter by standard (x12, edifact, hl7, custom, rosettanet, tradacoms, odette)
            classification: Filter by classification (tradingpartner, mycompany)
            folder_name: Filter by folder name

        Returns:
            List of trading partners grouped by standard with summary statistics
        """
        try:
            subject = TEST_USER
            print(f"[INFO] list_trading_partners called for local user: {subject}, profile: {profile}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            # Build filters
            filters = {}
            if standard:
                filters["standard"] = standard
            if classification:
                filters["classification"] = classification
            if folder_name:
                filters["folder_name"] = folder_name

            return trading_partner_tools.list_trading_partners(sdk, profile, filters)

        except Exception as e:
            print(f"[ERROR] Failed to list trading partners: {e}")
            return {"_success": False, "error": str(e)}

    @mcp.tool()
    def get_trading_partner(profile: str, component_id: str):
        """
        Get details of a specific trading partner by ID.

        Args:
            profile: Boomi profile name (required)
            component_id: Trading partner component ID

        Returns:
            Trading partner details including contact info and partner identifiers
        """
        try:
            subject = TEST_USER
            print(f"[INFO] get_trading_partner called for local user: {subject}, profile: {profile}, id: {component_id}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            return trading_partner_tools.get_trading_partner(sdk, profile, component_id)

        except Exception as e:
            print(f"[ERROR] Failed to get trading partner: {e}")
            return {"_success": False, "error": str(e)}

    @mcp.tool()
    def create_trading_partner(
        profile: str,
        component_name: str,
        standard: str = "x12",
        classification: str = "tradingpartner",
        folder_name: str = None,
        isa_id: str = None,
        isa_qualifier: str = None,
        gs_id: str = None,
        contact_name: str = None,
        contact_email: str = None,
        contact_phone: str = None
    ):
        """
        Create a new trading partner in Boomi.

        Args:
            profile: Boomi profile name (required)
            component_name: Name of the trading partner (required)
            standard: Trading standard (x12, edifact, hl7, custom, rosettanet, tradacoms, odette)
            classification: Classification (tradingpartner, mycompany)
            folder_name: Optional folder to place the partner in
            isa_id: ISA ID for X12 partners
            isa_qualifier: ISA Qualifier for X12 partners
            gs_id: GS ID for X12 partners
            contact_name: Contact person name
            contact_email: Contact email address
            contact_phone: Contact phone number

        Returns:
            Created trading partner details with component ID
        """
        try:
            subject = TEST_USER
            print(f"[INFO] create_trading_partner called for local user: {subject}, profile: {profile}, name: {component_name}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            # Build request data
            request_data = {
                "component_name": component_name,
                "standard": standard,
                "classification": classification
            }

            if folder_name:
                request_data["folder_name"] = folder_name

            # Add partner info for X12
            if standard.lower() == "x12" and (isa_id or isa_qualifier or gs_id):
                request_data["partner_info"] = {}
                if isa_id:
                    request_data["partner_info"]["isa_id"] = isa_id
                if isa_qualifier:
                    request_data["partner_info"]["isa_qualifier"] = isa_qualifier
                if gs_id:
                    request_data["partner_info"]["gs_id"] = gs_id

            # Add contact info
            if contact_name or contact_email or contact_phone:
                request_data["contact_info"] = {}
                if contact_name:
                    request_data["contact_info"]["name"] = contact_name
                if contact_email:
                    request_data["contact_info"]["email"] = contact_email
                if contact_phone:
                    request_data["contact_info"]["phone"] = contact_phone

            return trading_partner_tools.create_trading_partner(sdk, profile, request_data)

        except Exception as e:
            print(f"[ERROR] Failed to create trading partner: {e}")
            return {"_success": False, "error": str(e)}

    @mcp.tool()
    def update_trading_partner(
        profile: str,
        component_id: str,
        component_name: str = None,
        contact_name: str = None,
        contact_email: str = None,
        contact_phone: str = None,
        isa_id: str = None,
        isa_qualifier: str = None,
        gs_id: str = None
    ):
        """
        Update an existing trading partner.

        Args:
            profile: Boomi profile name (required)
            component_id: Trading partner component ID (required)
            component_name: New name for the partner
            contact_name: Updated contact name
            contact_email: Updated contact email
            contact_phone: Updated contact phone
            isa_id: Updated ISA ID (X12)
            isa_qualifier: Updated ISA Qualifier (X12)
            gs_id: Updated GS ID (X12)

        Returns:
            Updated trading partner details
        """
        try:
            subject = TEST_USER
            print(f"[INFO] update_trading_partner called for local user: {subject}, profile: {profile}, id: {component_id}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            # Build updates
            updates = {}
            if component_name:
                updates["component_name"] = component_name

            # Contact info updates
            if contact_name or contact_email or contact_phone:
                updates["contact_info"] = {}
                if contact_name:
                    updates["contact_info"]["name"] = contact_name
                if contact_email:
                    updates["contact_info"]["email"] = contact_email
                if contact_phone:
                    updates["contact_info"]["phone"] = contact_phone

            # Partner info updates
            if isa_id or isa_qualifier or gs_id:
                updates["partner_info"] = {}
                if isa_id:
                    updates["partner_info"]["isa_id"] = isa_id
                if isa_qualifier:
                    updates["partner_info"]["isa_qualifier"] = isa_qualifier
                if gs_id:
                    updates["partner_info"]["gs_id"] = gs_id

            return trading_partner_tools.update_trading_partner(sdk, profile, component_id, updates)

        except Exception as e:
            print(f"[ERROR] Failed to update trading partner: {e}")
            return {"_success": False, "error": str(e)}

    @mcp.tool()
    def delete_trading_partner(profile: str, component_id: str):
        """
        Delete a trading partner component.

        Args:
            profile: Boomi profile name (required)
            component_id: Trading partner component ID to delete

        Returns:
            Deletion confirmation
        """
        try:
            subject = TEST_USER
            print(f"[INFO] delete_trading_partner called for local user: {subject}, profile: {profile}, id: {component_id}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            return trading_partner_tools.delete_trading_partner(sdk, profile, component_id)

        except Exception as e:
            print(f"[ERROR] Failed to delete trading partner: {e}")
            return {"_success": False, "error": str(e)}

    @mcp.tool()
    def analyze_trading_partner_usage(profile: str, component_id: str):
        """
        Analyze where a trading partner is used in processes and configurations.

        Args:
            profile: Boomi profile name (required)
            component_id: Trading partner component ID to analyze

        Returns:
            Usage analysis including processes, connections, and dependencies
        """
        try:
            subject = TEST_USER
            print(f"[INFO] analyze_trading_partner_usage called for local user: {subject}, profile: {profile}, id: {component_id}")

            # Get credentials
            creds = get_secret(subject, profile)

            # Initialize Boomi SDK
            sdk = Boomi(
                account_id=creds["account_id"],
                username=creds["username"],
                password=creds["password"]
            )

            return trading_partner_tools.analyze_trading_partner_usage(sdk, profile, component_id)

        except Exception as e:
            print(f"[ERROR] Failed to analyze trading partner usage: {e}")
            return {"_success": False, "error": str(e)}

    print("[INFO] Trading partner tools registered successfully (local)")


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
    if trading_partner_tools:
        print("\n  🤝 Trading Partner Management:")
        print("  • list_trading_partners - List all trading partners with filtering")
        print("  • get_trading_partner - Get specific trading partner details")
        print("  • create_trading_partner - Create new trading partners (X12, EDIFACT, HL7, etc.)")
        print("  • update_trading_partner - Update trading partner information")
        print("  • delete_trading_partner - Delete a trading partner")
        print("  • analyze_trading_partner_usage - Analyze partner usage in processes")
    print("\n📝 Quick Start:")
    print("  1. Connect with: claude mcp add boomi-local stdio -- python server_local.py")
    print("  2. Use set_boomi_credentials to store your Boomi API credentials")
    print("  3. Use boomi_account_info to test API calls")
    print("=" * 60 + "\n")

    # Run in stdio mode for fast local testing
    mcp.run(transport="stdio")
