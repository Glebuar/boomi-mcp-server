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
import xml.etree.ElementTree as ET

# Import typed models for query operations
from boomi.models import (
    TradingPartnerComponentQueryConfig,
    TradingPartnerComponentQueryConfigQueryFilter,
    TradingPartnerComponentSimpleExpression,
    TradingPartnerComponentSimpleExpressionOperator,
    TradingPartnerComponentSimpleExpressionProperty
)


# ============================================================================
# Trading Partner CRUD Operations
# ============================================================================

def create_trading_partner(boomi_client, profile: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new trading partner component in Boomi using JSON-based TradingPartnerComponent API.

    This implementation uses the typed JSON models from the boomi-python SDK
    instead of XML templates, providing better type safety and maintainability.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        request_data: Trading partner configuration including:
            - component_name: Name of the trading partner (required)
            - standard: Trading standard - x12, edifact, hl7, rosettanet, custom, tradacoms, or odette (default: x12)
            - classification: Classification type (default: tradingpartner)
            - folder_name: Folder name (default: Home)
            - description: Component description (optional)

            # Contact Information (10 fields)
            - contact_name, contact_email, contact_phone, contact_fax
            - contact_address, contact_address2, contact_city, contact_state, contact_country, contact_postalcode

            # Communication Protocols
            - communication_protocols: Comma-separated list or list of protocols (ftp, sftp, http, as2, mllp, oftp, disk)

            # Protocol-specific fields (see trading_partner_builders.py for details)
            - disk_*, ftp_*, sftp_*, http_*, as2_*, oftp_*

            # Standard-specific fields (see trading_partner_builders.py for details)
            - isa_id, isa_qualifier, gs_id (X12)
            - unb_* (EDIFACT)
            - sending_*, receiving_* (HL7)
            - duns_number, global_location_number (RosettaNet)
            - sender_code, recipient_code (TRADACOMS)
            - originator_code, destination_code (ODETTE)
            - custom_partner_info (dict for custom standard)

    Returns:
        Created trading partner details or error

    Example:
        request_data = {
            "component_name": "My Trading Partner",
            "standard": "x12",
            "classification": "tradingpartner",
            "folder_name": "Home",
            "contact_email": "partner@example.com",
            "isa_id": "MYPARTNER",
            "isa_qualifier": "01",
            "communication_protocols": "http",
            "http_url": "https://partner.example.com/edi"
        }
    """
    try:
        # Import the JSON model builder
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
        from src.boomi_mcp.models.trading_partner_builders import build_trading_partner_model

        # Validate required fields
        if not request_data.get("component_name"):
            return {
                "_success": False,
                "error": "component_name is required",
                "message": "Trading partner name (component_name) is required"
            }

        # Extract main fields and pass remaining fields as kwargs
        component_name = request_data.get("component_name")
        standard = request_data.get("standard", "x12")
        classification = request_data.get("classification", "tradingpartner")
        folder_name = request_data.get("folder_name", "Home")
        description = request_data.get("description", "")

        # Remove main fields from request_data to avoid duplicate kwargs
        other_params = {k: v for k, v in request_data.items()
                       if k not in ["component_name", "standard", "classification", "folder_name", "description"]}

        # Check if we have complex protocols (FTP, SFTP, HTTP, AS2) that need raw dict
        protocols = request_data.get("communication_protocols", [])
        if isinstance(protocols, str):
            protocols = [p.strip().lower() for p in protocols.split(',') if p.strip()]
        complex_protocols = set(protocols) - {'disk'}

        if complex_protocols:
            # Use raw dict approach for FTP/SFTP/HTTP/AS2 (SDK models require too many nested objects)
            from boomi_mcp.models.trading_partner_builders import (
                build_partner_info, build_contact_info, build_partner_communication
            )

            payload = {
                'componentName': component_name,
                'standard': standard,
                'classification': classification,
                'folderName': folder_name
            }

            # Add partner info
            partner_info = build_partner_info(standard=standard, **other_params)
            if partner_info:
                payload['PartnerInfo'] = partner_info._map()

            # Add contact info
            contact_info = build_contact_info(**other_params)
            if contact_info:
                payload['ContactInfo'] = contact_info._map()

            # Add communication (returns dict wrapper for complex protocols)
            comm_params = {**other_params, 'communication_protocols': protocols}
            partner_comm = build_partner_communication(**comm_params)
            if partner_comm:
                payload['PartnerCommunication'] = partner_comm._map()

            # Use raw HTTP request (reuse boomi_client's credentials)
            import requests
            account_id = boomi_client.trading_partner_component.base_url.split('/')[-1]
            basic_auth = boomi_client.trading_partner_component.get_basic_auth()
            auth = (basic_auth._username, basic_auth._password)
            url = f"https://api.boomi.com/api/rest/v1/{account_id}/TradingPartnerComponent"
            r = requests.post(url, auth=auth, json=payload,
                            headers={'Content-Type': 'application/json', 'Accept': 'application/json'})

            if r.status_code != 200:
                return {
                    "_success": False,
                    "error": f"API error: {r.status_code}",
                    "message": f"Failed to create trading partner: {r.text[:500]}"
                }

            result_json = r.json()
            component_id = result_json.get('componentId')

            return {
                "_success": True,
                "trading_partner": {
                    "component_id": component_id,
                    "name": result_json.get('componentName', component_name),
                    "standard": standard,
                    "classification": classification,
                    "folder_name": result_json.get('folderName', folder_name)
                },
                "message": f"Successfully created trading partner: {component_name}"
            }

        # Standard path using SDK models (for Disk or no protocols)
        try:
            tp_model = build_trading_partner_model(
                component_name=component_name,
                standard=standard,
                classification=classification,
                folder_name=folder_name,
                description=description,
                **other_params  # Pass all other parameters
            )
        except ValueError as ve:
            return {
                "_success": False,
                "error": str(ve),
                "message": f"Invalid trading partner configuration: {str(ve)}"
            }

        # Create trading partner using TradingPartnerComponent API (JSON-based)
        result = boomi_client.trading_partner_component.create_trading_partner_component(
            request_body=tp_model
        )

        # Extract component ID using the same pattern as SDK example
        # SDK uses 'id_' attribute, not 'component_id'
        component_id = None
        if hasattr(result, 'id_'):
            component_id = result.id_
        elif hasattr(result, 'component_id'):
            component_id = result.component_id
        elif hasattr(result, 'id'):
            component_id = result.id

        return {
            "_success": True,
            "trading_partner": {
                "component_id": component_id,
                "name": getattr(result, 'name', request_data.get("component_name")),
                "standard": request_data.get("standard", "x12"),
                "classification": request_data.get("classification", "tradingpartner"),
                "folder_name": request_data.get("folder_name", "Home")
            },
            "message": f"Successfully created trading partner: {request_data.get('component_name')}"
        }

    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages for common issues
        if "B2B" in error_msg or "EDI" in error_msg:
            error_msg = f"{error_msg}. Note: Account must have B2B/EDI feature enabled for trading partner creation."

        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to create trading partner: {error_msg}"
        }


def get_trading_partner(boomi_client, profile: str, component_id: str) -> Dict[str, Any]:
    """
    Get details of a specific trading partner by ID.

    This implementation aligns with the boomi-python SDK example pattern,
    using id_ parameter and proper attribute access.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID

    Returns:
        Trading partner details or error
    """
    try:
        import xml.etree.ElementTree as ET

        # Use id_ parameter as shown in SDK example
        # If SDK parsing fails (due to FTP/SFTP/HTTP/AS2 model issues), fall back to raw HTTP
        used_raw_http = False
        result = None
        try:
            result = boomi_client.trading_partner_component.get_trading_partner_component(
                id_=component_id
            )
        except Exception as sdk_error:
            # SDK has issues with FTP/SFTP/HTTP/AS2 deserialization - use raw HTTP
            error_str = str(sdk_error)
            if any(x in error_str for x in ["FtpGetOptions", "SftpGetOptions", "HttpSettings", "HttpGetOptions", "As2", "ContactInfo"]):
                import requests
                account_id = boomi_client.trading_partner_component.base_url.split('/')[-1]
                basic_auth = boomi_client.trading_partner_component.get_basic_auth()
                auth = (basic_auth._username, basic_auth._password)
                url = f"https://api.boomi.com/api/rest/v1/{account_id}/TradingPartnerComponent/{component_id}"
                r = requests.get(url, auth=auth, headers={'Accept': 'application/json'})
                if r.status_code == 200:
                    used_raw_http = True
                    result = r.json()
                else:
                    raise
            else:
                raise

        # Handle result based on whether we used raw HTTP or SDK
        if used_raw_http:
            # Result is a dict from raw HTTP response
            retrieved_id = result.get('componentId', component_id)
            standard = result.get('standard')
            classification = result.get('classification')
            component_name = result.get('componentName')
            folder_id = result.get('folderId')
            folder_name = result.get('folderName')
            deleted = result.get('deleted', False)

            # Parse partner info from dict
            partner_info = {}
            info = result.get('PartnerInfo', {})
            if info:
                x12_info = info.get('X12PartnerInfo', {})
                if x12_info:
                    x12_ctrl = x12_info.get('X12ControlInfo', {})
                    if x12_ctrl:
                        isa_ctrl = x12_ctrl.get('ISAControlInfo', {})
                        gs_ctrl = x12_ctrl.get('GSControlInfo', {})
                        if isa_ctrl:
                            partner_info["isa_id"] = isa_ctrl.get('interchangeId')
                            partner_info["isa_qualifier"] = isa_ctrl.get('interchangeIdQualifier')
                        if gs_ctrl:
                            partner_info["gs_id"] = gs_ctrl.get('applicationcode')

            # Parse contact info from dict
            contact_info = {}
            contact = result.get('ContactInfo', {})
            if contact:
                raw_contact = {
                    "name": contact.get('contactName'),
                    "email": contact.get('email'),
                    "phone": contact.get('phone'),
                    "address1": contact.get('address1'),
                    "address2": contact.get('address2'),
                    "city": contact.get('city'),
                    "state": contact.get('state'),
                    "country": contact.get('country'),
                    "postalcode": contact.get('postalcode'),
                    "fax": contact.get('fax')
                }
                contact_info = {k: v for k, v in raw_contact.items() if v}

            # Parse communication protocols from dict
            communication_protocols = []
            comm = result.get('PartnerCommunication', {})
            if comm:
                # Disk protocol
                disk_opts = comm.get('DiskCommunicationOptions', {})
                if disk_opts:
                    disk_info = {"protocol": "disk"}
                    get_opts = disk_opts.get('DiskGetOptions', {})
                    send_opts = disk_opts.get('DiskSendOptions', {})
                    if get_opts:
                        disk_info["get_directory"] = get_opts.get('getDirectory')
                    if send_opts:
                        disk_info["send_directory"] = send_opts.get('sendDirectory')
                    communication_protocols.append(disk_info)

                # FTP protocol
                ftp_opts = comm.get('FTPCommunicationOptions', {})
                if ftp_opts:
                    ftp_info = {"protocol": "ftp"}
                    settings = ftp_opts.get('FTPSettings', {})
                    if settings:
                        ftp_info["host"] = settings.get('host')
                        # Port may come as ["BigInteger", 21] or just 21
                        port = settings.get('port')
                        if isinstance(port, list) and len(port) == 2:
                            port = port[1]
                        ftp_info["port"] = port
                        ftp_info["user"] = settings.get('user')
                    get_opts = ftp_opts.get('FTPGetOptions', {})
                    if get_opts:
                        ftp_info["remote_directory"] = get_opts.get('remoteDirectory')
                    communication_protocols.append(ftp_info)

                # SFTP protocol
                sftp_opts = comm.get('SFTPCommunicationOptions', {})
                if sftp_opts:
                    sftp_info = {"protocol": "sftp"}
                    settings = sftp_opts.get('SFTPSettings', {})
                    if settings:
                        sftp_info["host"] = settings.get('host')
                        # Port may come as ["BigInteger", 22] or just 22
                        port = settings.get('port')
                        if isinstance(port, list) and len(port) == 2:
                            port = port[1]
                        sftp_info["port"] = port
                        sftp_info["user"] = settings.get('user')
                    get_opts = sftp_opts.get('SFTPGetOptions', {})
                    if get_opts:
                        sftp_info["remote_directory"] = get_opts.get('remoteDirectory')
                    communication_protocols.append(sftp_info)

                # HTTP protocol
                http_opts = comm.get('HTTPCommunicationOptions', {})
                if http_opts:
                    http_info = {"protocol": "http"}
                    settings = http_opts.get('HTTPSettings', {})
                    if settings:
                        http_info["url"] = settings.get('url')
                        http_info["connect_timeout"] = settings.get('connectTimeout')
                        http_info["read_timeout"] = settings.get('readTimeout')
                    communication_protocols.append(http_info)

                # AS2 protocol
                as2_opts = comm.get('AS2CommunicationOptions', {})
                if as2_opts:
                    as2_info = {"protocol": "as2"}
                    settings = as2_opts.get('AS2SendSettings', {})
                    if settings:
                        as2_info["url"] = settings.get('url')
                    communication_protocols.append(as2_info)

                # MLLP protocol
                if comm.get('MLLPCommunicationOptions'):
                    communication_protocols.append({"protocol": "mllp"})

                # OFTP protocol
                if comm.get('OFTPCommunicationOptions'):
                    communication_protocols.append({"protocol": "oftp"})

            return {
                "_success": True,
                "trading_partner": {
                    "component_id": retrieved_id,
                    "name": component_name,
                    "standard": standard,
                    "classification": classification,
                    "folder_id": folder_id,
                    "folder_name": folder_name,
                    "deleted": deleted,
                    "partner_info": partner_info if partner_info else None,
                    "contact_info": contact_info if contact_info else None,
                    "communication_protocols": communication_protocols if communication_protocols else []
                }
            }

        # SDK model path - extract using getattr
        retrieved_id = None
        if hasattr(result, 'id_'):
            retrieved_id = result.id_
        elif hasattr(result, 'id'):
            retrieved_id = result.id
        elif hasattr(result, 'component_id'):
            retrieved_id = result.component_id
        else:
            retrieved_id = component_id

        # Extract partner details (use snake_case for JSON API attributes)
        partner_info = {}
        info = getattr(result, 'partner_info', None)
        if info:
            # X12 partner info
            x12_info = getattr(info, 'x12_partner_info', None)
            if x12_info:
                x12_ctrl = getattr(x12_info, 'x12_control_info', None)
                if x12_ctrl:
                    isa_ctrl = getattr(x12_ctrl, 'isa_control_info', None)
                    gs_ctrl = getattr(x12_ctrl, 'gs_control_info', None)
                    if isa_ctrl:
                        partner_info["isa_id"] = getattr(isa_ctrl, 'interchange_id', None)
                        partner_info["isa_qualifier"] = getattr(isa_ctrl, 'interchange_id_qualifier', None)
                    if gs_ctrl:
                        partner_info["gs_id"] = getattr(gs_ctrl, 'applicationcode', None)

        contact_info = {}
        communication_protocols = []

        # Use object attributes for SDK model
        contact = getattr(result, 'contact_info', None)
        if contact:
            raw_contact = {
                "name": getattr(contact, 'contact_name', None),
                "email": getattr(contact, 'email', None),
                "phone": getattr(contact, 'phone', None),
                "address1": getattr(contact, 'address1', None),
                "address2": getattr(contact, 'address2', None),
                "city": getattr(contact, 'city', None),
                "state": getattr(contact, 'state', None),
                "country": getattr(contact, 'country', None),
                "postalcode": getattr(contact, 'postalcode', None),
                "fax": getattr(contact, 'fax', None)
            }
            contact_info = {k: v for k, v in raw_contact.items() if v}

        # Parse partner_communication for communication protocols
        comm = getattr(result, 'partner_communication', None)
        if comm:
            # Disk protocol
            if getattr(comm, 'disk_communication_options', None):
                disk_opts = comm.disk_communication_options
                disk_info = {"protocol": "disk"}
                get_opts = getattr(disk_opts, 'disk_get_options', None)
                send_opts = getattr(disk_opts, 'disk_send_options', None)
                if get_opts:
                    disk_info["get_directory"] = getattr(get_opts, 'get_directory', None)
                    disk_info["file_filter"] = getattr(get_opts, 'file_filter', None)
                if send_opts:
                    disk_info["send_directory"] = getattr(send_opts, 'send_directory', None)
                communication_protocols.append(disk_info)

            # FTP protocol
            if getattr(comm, 'ftp_communication_options', None):
                ftp_opts = comm.ftp_communication_options
                ftp_info = {"protocol": "ftp"}
                settings = getattr(ftp_opts, 'ftp_settings', None)
                if settings:
                    ftp_info["host"] = getattr(settings, 'host', None)
                    ftp_info["port"] = getattr(settings, 'port', None)
                    ftp_info["user"] = getattr(settings, 'user', None)
                get_opts = getattr(ftp_opts, 'ftp_get_options', None)
                if get_opts:
                    ftp_info["remote_directory"] = getattr(get_opts, 'remote_directory', None)
                communication_protocols.append(ftp_info)

            # SFTP protocol
            if getattr(comm, 'sftp_communication_options', None):
                sftp_opts = comm.sftp_communication_options
                sftp_info = {"protocol": "sftp"}
                settings = getattr(sftp_opts, 'sftp_settings', None)
                if settings:
                    sftp_info["host"] = getattr(settings, 'host', None)
                    sftp_info["port"] = getattr(settings, 'port', None)
                    sftp_info["user"] = getattr(settings, 'user', None)
                get_opts = getattr(sftp_opts, 'sftp_get_options', None)
                if get_opts:
                    sftp_info["remote_directory"] = getattr(get_opts, 'remote_directory', None)
                communication_protocols.append(sftp_info)

            # HTTP protocol
            if getattr(comm, 'http_communication_options', None):
                http_opts = comm.http_communication_options
                http_info = {"protocol": "http"}
                settings = getattr(http_opts, 'http_settings', None)
                if settings:
                    http_info["url"] = getattr(settings, 'url', None)
                    http_info["connect_timeout"] = getattr(settings, 'connect_timeout', None)
                    http_info["read_timeout"] = getattr(settings, 'read_timeout', None)
                communication_protocols.append(http_info)

            # AS2 protocol
            if getattr(comm, 'as2_communication_options', None):
                as2_opts = comm.as2_communication_options
                as2_info = {"protocol": "as2"}
                settings = getattr(as2_opts, 'as2_send_settings', None)
                if settings:
                    as2_info["url"] = getattr(settings, 'url', None)
                communication_protocols.append(as2_info)

            # MLLP protocol
            if getattr(comm, 'mllp_communication_options', None):
                communication_protocols.append({"protocol": "mllp"})

            # OFTP protocol
            if getattr(comm, 'oftp_communication_options', None):
                communication_protocols.append({"protocol": "oftp"})

        return {
            "_success": True,
            "trading_partner": {
                "component_id": retrieved_id,
                "name": getattr(result, 'name', getattr(result, 'component_name', None)),
                "standard": getattr(result, 'standard', None),
                "classification": getattr(result, 'classification', None),
                "folder_id": getattr(result, 'folder_id', None),
                "folder_name": getattr(result, 'folder_name', None),
                "organization_id": getattr(result, 'organization_id', None),
                "deleted": getattr(result, 'deleted', False),
                "partner_info": partner_info if partner_info else None,
                "contact_info": contact_info if contact_info else None,
                "communication_protocols": communication_protocols if communication_protocols else []
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
    List all trading partners with optional filtering using typed query models.

    This implementation follows the boomi-python SDK example pattern of using
    typed query model classes instead of dictionary-based queries.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        filters: Optional filters including:
            - standard: Filter by standard (x12, edifact, hl7, etc.)
            - classification: Filter by classification (tradingpartner, mycompany)
            - folder_name: Filter by folder
            - name_pattern: Filter by name pattern (supports % wildcard)
            - include_deleted: Include deleted partners (default: False)

    Returns:
        List of trading partners or error
    """
    try:
        # Build query expression using typed models (as shown in SDK example)
        expressions = []

        if filters:
            # Filter by standard
            if "standard" in filters:
                expr = TradingPartnerComponentSimpleExpression(
                    operator=TradingPartnerComponentSimpleExpressionOperator.EQUALS,
                    property=TradingPartnerComponentSimpleExpressionProperty.STANDARD,
                    argument=[filters["standard"].lower()]
                )
                expressions.append(expr)

            # Filter by classification
            if "classification" in filters:
                expr = TradingPartnerComponentSimpleExpression(
                    operator=TradingPartnerComponentSimpleExpressionOperator.EQUALS,
                    property=TradingPartnerComponentSimpleExpressionProperty.CLASSIFICATION,
                    argument=[filters["classification"].lower()]
                )
                expressions.append(expr)

            # Filter by name pattern
            if "name_pattern" in filters:
                expr = TradingPartnerComponentSimpleExpression(
                    operator=TradingPartnerComponentSimpleExpressionOperator.LIKE,
                    property=TradingPartnerComponentSimpleExpressionProperty.NAME,
                    argument=[filters["name_pattern"]]
                )
                expressions.append(expr)

            # Note: NOT_EQUALS operator not available in typed models
            # Deleted filtering would need to be done client-side if needed

        # If no filters provided, get all trading partners
        if not expressions:
            expression = TradingPartnerComponentSimpleExpression(
                operator=TradingPartnerComponentSimpleExpressionOperator.LIKE,
                property=TradingPartnerComponentSimpleExpressionProperty.NAME,
                argument=['%']
            )
        elif len(expressions) == 1:
            expression = expressions[0]
        else:
            # Multiple expressions - would need to use compound expression
            # For now, use the first expression
            # TODO: Implement compound expression support if needed
            expression = expressions[0]

        # Build typed query config
        query_filter = TradingPartnerComponentQueryConfigQueryFilter(expression=expression)
        query_config = TradingPartnerComponentQueryConfig(query_filter=query_filter)

        # Query trading partners using typed config
        result = boomi_client.trading_partner_component.query_trading_partner_component(
            request_body=query_config
        )

        partners = []
        if hasattr(result, 'result') and result.result:
            for partner in result.result:
                # Extract ID using SDK pattern (id_ attribute)
                partner_id = None
                if hasattr(partner, 'id_'):
                    partner_id = partner.id_
                elif hasattr(partner, 'id'):
                    partner_id = partner.id
                elif hasattr(partner, 'component_id'):
                    partner_id = partner.component_id

                partners.append({
                    "component_id": partner_id,
                    "name": getattr(partner, 'name', getattr(partner, 'component_name', None)),
                    "standard": getattr(partner, 'standard', None),
                    "classification": getattr(partner, 'classification', None),
                    "folder_name": getattr(partner, 'folder_name', None),
                    "deleted": getattr(partner, 'deleted', False)
                })

        # Group partners by standard
        grouped = {}
        for partner in partners:
            standard = partner.get("standard", "unknown")
            if standard:
                standard_upper = standard.upper()
                if standard_upper not in grouped:
                    grouped[standard_upper] = []
                grouped[standard_upper].append(partner)

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
    Update an existing trading partner component using JSON-based TradingPartnerComponent API.

    This implementation uses the typed JSON models for a much simpler update process:
    1. Get existing trading partner using trading_partner_component.get_trading_partner_component()
    2. Update the model fields based on the updates dict
    3. Call trading_partner_component.update_trading_partner_component() with updated model

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID to update
        updates: Fields to update including:
            - component_name: Trading partner name
            - description: Component description
            - classification: Partner type (tradingpartner or mycompany)
            - folder_name: Folder location

            # Contact Information
            - contact_name, contact_email, contact_phone, contact_fax
            - contact_address, contact_address2, contact_city, contact_state, contact_country, contact_postalcode

            # Communication Protocols (not yet fully implemented)
            - communication_protocols: List of protocols
            - Protocol-specific fields (disk_*, ftp_*, sftp_*, http_*, as2_*, oftp_*)

            # Standard-specific fields (not yet fully implemented)
            - isa_id, isa_qualifier, gs_id (X12)
            - unb_* (EDIFACT)
            - sending_*, receiving_* (HL7)
            - etc.

    Returns:
        Updated trading partner details or error

    Note:
        Full implementation of protocol-specific and standard-specific updates
        will be added in future iterations. Currently supports basic fields.
    """
    try:
        # Import the JSON model builder
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
        from src.boomi_mcp.models.trading_partner_builders import build_contact_info
        from boomi.models import ContactInfo

        # Step 1: Get the existing trading partner using JSON-based API
        try:
            existing_tp = boomi_client.trading_partner_component.get_trading_partner_component(
                id_=component_id
            )
        except Exception as e:
            return {
                "_success": False,
                "error": f"Component not found: {str(e)}",
                "message": f"Trading partner {component_id} not found or could not be retrieved"
            }

        # Step 2: Update model fields based on updates dict
        # Note: Currently only basic fields are supported.
        # Protocol-specific and standard-specific updates will be added in future iterations.

        # Update basic component fields
        if "component_name" in updates:
            existing_tp.component_name = updates["component_name"]

        if "description" in updates:
            existing_tp.description = updates["description"]

        if "classification" in updates:
            from boomi.models import TradingPartnerComponentClassification
            classification = updates["classification"]
            if isinstance(classification, str):
                if classification.lower() == "mycompany":
                    existing_tp.classification = TradingPartnerComponentClassification.MYCOMPANY
                else:
                    existing_tp.classification = TradingPartnerComponentClassification.TRADINGPARTNER
            else:
                existing_tp.classification = classification

        if "folder_name" in updates:
            existing_tp.folder_name = updates["folder_name"]

        # Update contact information
        # Support both nested dict format and flat parameter format
        contact_updates = {}
        if "contact_info" in updates:
            # Nested format
            contact_updates = updates["contact_info"]
        else:
            # Flat format - extract contact_* parameters
            for key in updates:
                if key.startswith('contact_'):
                    contact_updates[key] = updates[key]

        if contact_updates:
            # Build ContactInfo model from updates
            contact_info = build_contact_info(**contact_updates)
            if contact_info:
                existing_tp.contact_info = contact_info

        # TODO: Protocol-specific updates (disk_*, ftp_*, sftp_*, http_*, as2_*, oftp_*)
        # TODO: Standard-specific updates (isa_*, unb_*, sending_*, receiving_*, etc.)
        # These will require implementing the protocol and standard builders in trading_partner_builders.py

        # Step 3: Update the trading partner using JSON-based API
        result = boomi_client.trading_partner_component.update_trading_partner_component(
            id_=component_id,
            request_body=existing_tp
        )

        return {
            "_success": True,
            "trading_partner": {
                "component_id": component_id,
                "name": updates.get("component_name", getattr(component, 'name', None)),
                "updated_fields": list(updates.keys())
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

    Uses the ComponentReference API to find all components that reference this trading partner.
    Note: Returns immediate references (one level), not recursive like UI's "Show Where Used".

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID

    Returns:
        Usage analysis including processes, connections, and dependencies
    """
    try:
        # Get the trading partner details first using Component API (avoids ContactInfo parsing issues)
        partner = boomi_client.component.get_component(component_id=component_id)
        partner_name = getattr(partner, 'name', 'Unknown')

        # Query for component references using the QUERY endpoint (returns 200 with empty results, not 400)
        from boomi.models import (
            ComponentReferenceQueryConfig,
            ComponentReferenceQueryConfigQueryFilter,
            ComponentReferenceSimpleExpression,
            ComponentReferenceSimpleExpressionOperator,
            ComponentReferenceSimpleExpressionProperty
        )

        # Build query to find all components that reference this trading partner
        expression = ComponentReferenceSimpleExpression(
            operator=ComponentReferenceSimpleExpressionOperator.EQUALS,
            property=ComponentReferenceSimpleExpressionProperty.COMPONENTID,
            argument=[component_id]
        )
        query_filter = ComponentReferenceQueryConfigQueryFilter(expression=expression)
        query_config = ComponentReferenceQueryConfig(query_filter=query_filter)

        # Execute query
        query_result = boomi_client.component_reference.query_component_reference(request_body=query_config)

        # Collect all referenced components
        referenced_by = []

        # Extract references from query results
        if hasattr(query_result, 'result') and query_result.result:
            for result_item in query_result.result:
                # Each result item has a 'references' array
                refs = getattr(result_item, 'references', [])
                if not refs:
                    continue

                for ref in refs:
                    parent_id = getattr(ref, 'parent_component_id', None)
                    parent_version = getattr(ref, 'parent_version', None)

                    if parent_id:
                        # Try to get component metadata
                        try:
                            parent_comp = boomi_client.component.get_component(component_id=parent_id)
                            comp_type = getattr(parent_comp, 'type', 'unknown')
                            comp_name = getattr(parent_comp, 'name', 'Unknown')

                            referenced_by.append({
                                "component_id": parent_id,
                                "name": comp_name,
                                "type": comp_type,
                                "version": str(parent_version)
                            })
                        except Exception as e:
                            # If we can't get parent component details, still include the reference
                            referenced_by.append({
                                "component_id": parent_id,
                                "name": "Unknown",
                                "type": "unknown",
                                "version": str(parent_version),
                                "error": str(e)
                            })

        analysis = {
            "_success": True,
            "trading_partner": {
                "component_id": component_id,
                "name": partner_name,
                "standard": getattr(partner, 'standard', None)
            },
            "referenced_by": referenced_by,
            "total_references": len(referenced_by),
            "can_safely_delete": len(referenced_by) == 0,
            "_note": "Shows immediate references (one level). UI's 'Show Where Used' does recursive tracing."
        }

        return analysis

    except Exception as e:
        return {
            "_success": False,
            "error": str(e),
            "message": f"Failed to analyze trading partner usage: {str(e)}"
        }


# ============================================================================
# Consolidated Action Router (for MCP tool consolidation)
# ============================================================================

def manage_trading_partner_action(
    boomi_client,
    profile: str,
    action: str,
    **params
) -> Dict[str, Any]:
    """
    Consolidated trading partner management function.

    Routes to appropriate function based on action parameter.
    This enables consolidation of 6 separate MCP tools into 1.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        action: Action to perform (list, get, create, update, delete, analyze_usage)
        **params: Action-specific parameters

    Actions:
        - list: List trading partners with optional filters
          Params: filters (optional dict)

        - get: Get specific trading partner by ID
          Params: partner_id (required str)

        - create: Create new trading partner
          Params: request_data (required dict with standard, name, etc.)

        - update: Update existing trading partner
          Params: partner_id (required str), updates (required dict)

        - delete: Delete trading partner
          Params: partner_id (required str)

        - analyze_usage: Analyze where trading partner is used
          Params: partner_id (required str)

    Returns:
        Action result dict with success status and data/error
    """
    try:
        if action == "list":
            filters = params.get("filters", None)
            return list_trading_partners(boomi_client, profile, filters)

        elif action == "get":
            partner_id = params.get("partner_id")
            if not partner_id:
                return {
                    "_success": False,
                    "error": "partner_id is required for 'get' action",
                    "hint": "Provide the trading partner component ID to retrieve"
                }
            return get_trading_partner(boomi_client, profile, partner_id)

        elif action == "create":
            request_data = params.get("request_data")
            if not request_data:
                return {
                    "_success": False,
                    "error": "request_data is required for 'create' action",
                    "hint": "Provide trading partner configuration including standard, name, and standard-specific parameters. Use get_schema_template for expected format."
                }
            return create_trading_partner(boomi_client, profile, request_data)

        elif action == "update":
            partner_id = params.get("partner_id")
            updates = params.get("updates")
            if not partner_id:
                return {
                    "_success": False,
                    "error": "partner_id is required for 'update' action",
                    "hint": "Provide the trading partner component ID to update"
                }
            if not updates:
                return {
                    "_success": False,
                    "error": "updates dict is required for 'update' action",
                    "hint": "Provide the fields to update in the trading partner configuration"
                }
            return update_trading_partner(boomi_client, profile, partner_id, updates)

        elif action == "delete":
            partner_id = params.get("partner_id")
            if not partner_id:
                return {
                    "_success": False,
                    "error": "partner_id is required for 'delete' action",
                    "hint": "Provide the trading partner component ID to delete"
                }
            return delete_trading_partner(boomi_client, profile, partner_id)

        elif action == "analyze_usage":
            partner_id = params.get("partner_id")
            if not partner_id:
                return {
                    "_success": False,
                    "error": "partner_id is required for 'analyze_usage' action",
                    "hint": "Provide the trading partner component ID to analyze"
                }
            return analyze_trading_partner_usage(boomi_client, profile, partner_id)

        else:
            return {
                "_success": False,
                "error": f"Unknown action: {action}",
                "hint": "Valid actions are: list, get, create, update, delete, analyze_usage"
            }

    except Exception as e:
        return {
            "_success": False,
            "error": f"Action '{action}' failed: {str(e)}",
            "exception_type": type(e).__name__
        }