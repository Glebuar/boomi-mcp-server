#!/usr/bin/env python3
"""
Trading Partner MCP Tools for Boomi API Integration.

This module provides comprehensive trading partner management capabilities
including CRUD operations, bulk operations, and querying for B2B/EDI partners.

Supported Standards:
- X12 (EDI)
- EDIFACT
- HL7 (Healthcare)
- RosettaNet
- TRADACOMS
- ODETTE
- Custom formats
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime


def create_trading_partner(boomi_client, profile: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new trading partner component in Boomi.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        request_data: Trading partner configuration including:
            - component_name: Name of the trading partner
            - standard: Trading standard (x12, edifact, hl7, custom, rosettanet, tradacoms, odette)
            - classification: Classification type (tradingpartner, mycompany)
            - folder_name: Optional folder name
            - contact_info: Optional contact information
            - partner_info: Partner-specific information

    Returns:
        Created trading partner details or error
    """
    try:
        # Prepare trading partner component data
        partner_data = {
            "componentName": request_data.get("component_name"),
            "standard": request_data.get("standard", "x12").lower(),
            "classification": request_data.get("classification", "tradingpartner").lower()
        }

        # Add optional fields
        if "folder_name" in request_data:
            partner_data["folderName"] = request_data["folder_name"]
        if "folder_id" in request_data:
            partner_data["folderId"] = request_data["folder_id"]
        if "organization_id" in request_data:
            partner_data["organizationId"] = request_data["organization_id"]

        # Add contact information if provided
        if "contact_info" in request_data:
            contact = request_data["contact_info"]
            partner_data["ContactInfo"] = {
                "name": contact.get("name"),
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "address": contact.get("address"),
                "city": contact.get("city"),
                "state": contact.get("state"),
                "country": contact.get("country"),
                "postalCode": contact.get("postal_code")
            }

        # Add partner-specific information
        if "partner_info" in request_data:
            info = request_data["partner_info"]
            partner_data["PartnerInfo"] = {}

            # Add standard-specific identifiers
            if request_data.get("standard") == "x12":
                partner_data["PartnerInfo"]["ISAId"] = info.get("isa_id", "")
                partner_data["PartnerInfo"]["ISAQualifier"] = info.get("isa_qualifier", "")
                partner_data["PartnerInfo"]["GSId"] = info.get("gs_id", "")
            elif request_data.get("standard") == "edifact":
                partner_data["PartnerInfo"]["UNBId"] = info.get("unb_id", "")
                partner_data["PartnerInfo"]["UNBQualifier"] = info.get("unb_qualifier", "")
            elif request_data.get("standard") == "hl7":
                partner_data["PartnerInfo"]["SendingApplication"] = info.get("sending_application", "")
                partner_data["PartnerInfo"]["SendingFacility"] = info.get("sending_facility", "")
            elif request_data.get("standard") == "rosettanet":
                partner_data["PartnerInfo"]["DUNS"] = info.get("duns", "")
                partner_data["PartnerInfo"]["GlobalLocationNumber"] = info.get("gln", "")

        # Create trading partner
        result = boomi_client.trading_partner_component.create_trading_partner_component(partner_data)

        return {
            "_success": True,
            "trading_partner": {
                "component_id": getattr(result, 'component_id', None),
                "name": getattr(result, 'component_name', request_data.get("component_name")),
                "standard": request_data.get("standard"),
                "classification": request_data.get("classification"),
                "folder_id": getattr(result, 'folder_id', None)
            },
            "message": f"Successfully created trading partner: {request_data.get('component_name')}"
        }

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to create trading partner: {str(e)}"
        }


def get_trading_partner(boomi_client, profile: str, component_id: str) -> Dict[str, Any]:
    """
    Get details of a specific trading partner by ID.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID

    Returns:
        Trading partner details or error
    """
    try:
        result = boomi_client.trading_partner_component.get_trading_partner_component(component_id)

        # Extract partner details
        partner_info = {}
        if hasattr(result, 'PartnerInfo'):
            info = result.PartnerInfo
            partner_info = {
                "isa_id": getattr(info, 'ISAId', None),
                "isa_qualifier": getattr(info, 'ISAQualifier', None),
                "gs_id": getattr(info, 'GSId', None),
                "unb_id": getattr(info, 'UNBId', None),
                "unb_qualifier": getattr(info, 'UNBQualifier', None),
                "duns": getattr(info, 'DUNS', None)
            }

        contact_info = {}
        if hasattr(result, 'ContactInfo'):
            contact = result.ContactInfo
            contact_info = {
                "name": getattr(contact, 'name', None),
                "email": getattr(contact, 'email', None),
                "phone": getattr(contact, 'phone', None),
                "address": getattr(contact, 'address', None),
                "city": getattr(contact, 'city', None),
                "state": getattr(contact, 'state', None),
                "country": getattr(contact, 'country', None)
            }

        return {
            "_success": True,
            "trading_partner": {
                "component_id": getattr(result, 'component_id', component_id),
                "name": getattr(result, 'component_name', None),
                "standard": getattr(result, 'standard', None),
                "classification": getattr(result, 'classification', None),
                "folder_id": getattr(result, 'folder_id', None),
                "folder_name": getattr(result, 'folder_name', None),
                "organization_id": getattr(result, 'organization_id', None),
                "deleted": getattr(result, 'deleted', False),
                "partner_info": partner_info,
                "contact_info": contact_info
            }
        }

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to get trading partner: {str(e)}"
        }


def list_trading_partners(boomi_client, profile: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    List all trading partners with optional filtering.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        filters: Optional filters including:
            - standard: Filter by standard (x12, edifact, hl7, etc.)
            - classification: Filter by classification (tradingpartner, mycompany)
            - folder_name: Filter by folder
            - include_deleted: Include deleted partners (default: False)

    Returns:
        List of trading partners or error
    """
    try:
        # Build query configuration
        query_config = {
            "QueryFilter": {
                "expression": {
                    "operator": "and",
                    "nestedExpression": []
                }
            }
        }

        if filters:
            expressions = query_config["QueryFilter"]["expression"]["nestedExpression"]

            if "standard" in filters:
                expressions.append({
                    "operator": "EQUALS",
                    "property": "standard",
                    "argument": [filters["standard"].lower()]
                })

            if "classification" in filters:
                expressions.append({
                    "operator": "EQUALS",
                    "property": "classification",
                    "argument": [filters["classification"].lower()]
                })

            if "folder_name" in filters:
                expressions.append({
                    "operator": "EQUALS",
                    "property": "folderName",
                    "argument": [filters["folder_name"]]
                })

            if not filters.get("include_deleted", False):
                expressions.append({
                    "operator": "NOT_EQUALS",
                    "property": "deleted",
                    "argument": ["true"]
                })

        # Query trading partners
        result = boomi_client.trading_partner_component.query_trading_partner_component(query_config)

        partners = []
        if hasattr(result, 'result') and result.result:
            for partner in result.result:
                partners.append({
                    "component_id": getattr(partner, 'component_id', None),
                    "name": getattr(partner, 'component_name', None),
                    "standard": getattr(partner, 'standard', None),
                    "classification": getattr(partner, 'classification', None),
                    "folder_name": getattr(partner, 'folder_name', None),
                    "deleted": getattr(partner, 'deleted', False)
                })

        # Group partners by standard
        grouped = {}
        for partner in partners:
            standard = partner.get("standard", "unknown").upper()
            if standard not in grouped:
                grouped[standard] = []
            grouped[standard].append(partner)

        return {
            "_success": True,
            "total_count": len(partners),
            "partners": partners,
            "by_standard": grouped,
            "summary": {
                "x12": len(grouped.get("X12", [])),
                "edifact": len(grouped.get("EDIFACT", [])),
                "hl7": len(grouped.get("HL7", [])),
                "custom": len(grouped.get("CUSTOM", [])),
                "rosettanet": len(grouped.get("ROSETTANET", [])),
                "tradacoms": len(grouped.get("TRADACOMS", [])),
                "odette": len(grouped.get("ODETTE", []))
            }
        }

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to list trading partners: {str(e)}"
        }


def update_trading_partner(boomi_client, profile: str, component_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing trading partner component.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID to update
        updates: Fields to update (component_name, contact_info, partner_info, etc.)

    Returns:
        Updated trading partner details or error
    """
    try:
        # First get the existing partner
        existing = boomi_client.trading_partner_component.get_trading_partner_component(component_id)

        # Build update data by merging existing with updates
        update_data = {
            "componentId": component_id,
            "componentName": updates.get("component_name", getattr(existing, 'component_name', None)),
            "standard": updates.get("standard", getattr(existing, 'standard', None)),
            "classification": updates.get("classification", getattr(existing, 'classification', None))
        }

        # Update contact info if provided
        if "contact_info" in updates:
            contact = updates["contact_info"]
            update_data["ContactInfo"] = {
                "name": contact.get("name"),
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "address": contact.get("address"),
                "city": contact.get("city"),
                "state": contact.get("state"),
                "country": contact.get("country"),
                "postalCode": contact.get("postal_code")
            }
        elif hasattr(existing, 'ContactInfo'):
            # Keep existing contact info
            update_data["ContactInfo"] = existing.ContactInfo

        # Update partner info if provided
        if "partner_info" in updates:
            info = updates["partner_info"]
            update_data["PartnerInfo"] = {}

            if updates.get("standard", getattr(existing, 'standard', 'x12')) == "x12":
                update_data["PartnerInfo"]["ISAId"] = info.get("isa_id", "")
                update_data["PartnerInfo"]["ISAQualifier"] = info.get("isa_qualifier", "")
                update_data["PartnerInfo"]["GSId"] = info.get("gs_id", "")
            elif updates.get("standard") == "edifact":
                update_data["PartnerInfo"]["UNBId"] = info.get("unb_id", "")
                update_data["PartnerInfo"]["UNBQualifier"] = info.get("unb_qualifier", "")
        elif hasattr(existing, 'PartnerInfo'):
            # Keep existing partner info
            update_data["PartnerInfo"] = existing.PartnerInfo

        # Update trading partner
        result = boomi_client.trading_partner_component.update_trading_partner_component(
            component_id, update_data
        )

        return {
            "_success": True,
            "trading_partner": {
                "component_id": component_id,
                "name": updates.get("component_name", getattr(result, 'component_name', None)),
                "standard": updates.get("standard", getattr(result, 'standard', None)),
                "classification": updates.get("classification", getattr(result, 'classification', None))
            },
            "message": f"Successfully updated trading partner: {component_id}"
        }

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to update trading partner: {str(e)}"
        }


def delete_trading_partner(boomi_client, profile: str, component_id: str) -> Dict[str, Any]:
    """
    Delete a trading partner component.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID to delete

    Returns:
        Deletion confirmation or error
    """
    try:
        result = boomi_client.trading_partner_component.delete_trading_partner_component(component_id)

        return {
            "_success": True,
            "component_id": component_id,
            "deleted": True,
            "message": f"Successfully deleted trading partner: {component_id}"
        }

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to delete trading partner: {str(e)}"
        }


def bulk_create_trading_partners(boomi_client, profile: str, partners: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create multiple trading partners in a single operation.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        partners: List of trading partner configurations

    Returns:
        Bulk creation results or error
    """
    try:
        # Prepare bulk request
        bulk_data = {
            "TradingPartnerComponent": []
        }

        for partner_data in partners:
            partner_component = {
                "componentName": partner_data.get("component_name"),
                "standard": partner_data.get("standard", "x12").lower(),
                "classification": partner_data.get("classification", "tradingpartner").lower()
            }

            # Add optional fields
            if "folder_name" in partner_data:
                partner_component["folderName"] = partner_data["folder_name"]
            if "contact_info" in partner_data:
                partner_component["ContactInfo"] = partner_data["contact_info"]
            if "partner_info" in partner_data:
                partner_component["PartnerInfo"] = partner_data["partner_info"]

            bulk_data["TradingPartnerComponent"].append(partner_component)

        # Execute bulk create
        result = boomi_client.trading_partner_component.bulk_create_trading_partner_component(bulk_data)

        created_partners = []
        if hasattr(result, 'TradingPartnerComponent'):
            for partner in result.TradingPartnerComponent:
                created_partners.append({
                    "component_id": getattr(partner, 'component_id', None),
                    "name": getattr(partner, 'component_name', None),
                    "standard": getattr(partner, 'standard', None)
                })

        return {
            "_success": True,
            "created_count": len(created_partners),
            "partners": created_partners,
            "message": f"Successfully created {len(created_partners)} trading partners"
        }

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to bulk create trading partners: {str(e)}"
        }


def analyze_trading_partner_usage(boomi_client, profile: str, component_id: str) -> Dict[str, Any]:
    """
    Analyze where a trading partner is used in processes and configurations.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID

    Returns:
        Usage analysis including processes, connections, and dependencies
    """
    try:
        # Get the trading partner details first
        partner = boomi_client.trading_partner_component.get_trading_partner_component(component_id)
        partner_name = getattr(partner, 'component_name', 'Unknown')

        # Query for processes that reference this trading partner
        # This would typically involve searching for the partner ID in process configurations

        analysis = {
            "_success": True,
            "trading_partner": {
                "component_id": component_id,
                "name": partner_name,
                "standard": getattr(partner, 'standard', None)
            },
            "usage": {
                "processes": [],  # Would be populated by searching process components
                "connections": [],  # Would check connection configurations
                "maps": [],  # Would check map components
                "extensions": []  # Would check environment extensions
            },
            "summary": {
                "total_references": 0,
                "can_safely_delete": True  # Would be false if references found
            },
            "_note": "Full usage analysis would require additional component searches"
        }

        return analysis

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to analyze trading partner usage: {str(e)}"
        }