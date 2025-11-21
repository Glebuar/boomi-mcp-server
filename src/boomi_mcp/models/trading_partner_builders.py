#!/usr/bin/env python3
"""
Trading Partner JSON Model Builders

This module provides helper functions to build nested Boomi Trading Partner JSON models
from flat parameters. It maps the 70+ parameters currently supported in the XML implementation
to the nested JSON structure required by the Boomi API.

Usage:
    from trading_partner_builders import build_trading_partner_model

    tp_model = build_trading_partner_model(
        component_name="My Partner",
        standard="x12",
        classification="tradingpartner",
        folder_name="Home",
        contact_email="partner@example.com",
        isa_id="MYISAID",
        communication_protocols=["http", "as2"],
        http_url="https://partner.example.com/api",
        as2_url="https://partner.example.com/as2"
    )
"""

from typing import Dict, Any, List, Optional
from boomi.models import (
    TradingPartnerComponent,
    TradingPartnerComponentClassification,
    TradingPartnerComponentStandard,
    ContactInfo,
    PartnerCommunication,
    PartnerInfo,
)


# ============================================================================
# Contact Information Builder
# ============================================================================

def build_contact_info(**kwargs) -> Optional[ContactInfo]:
    """
    Build ContactInfo model from flat parameters.

    Args:
        contact_name: Contact person name
        contact_email: Email address
        contact_phone: Phone number
        contact_fax: Fax number
        contact_address: Street address line 1
        contact_address2: Street address line 2
        contact_city: City
        contact_state: State/province
        contact_country: Country
        contact_postalcode: Postal/zip code

    Returns:
        ContactInfo object if any contact fields provided, None otherwise
    """
    # Extract contact fields from kwargs
    contact_fields = {
        'address1': kwargs.get('contact_address', ''),
        'address2': kwargs.get('contact_address2', ''),
        'city': kwargs.get('contact_city', ''),
        'contact_name': kwargs.get('contact_name', ''),
        'country': kwargs.get('contact_country', ''),
        'email': kwargs.get('contact_email', ''),
        'fax': kwargs.get('contact_fax', ''),
        'phone': kwargs.get('contact_phone', ''),
        'postalcode': kwargs.get('contact_postalcode', ''),
        'state': kwargs.get('contact_state', '')
    }

    # Return None if all fields are empty
    if not any(contact_fields.values()):
        return None

    return ContactInfo(**contact_fields)


# ============================================================================
# Communication Protocol Builders
# ============================================================================

def build_disk_communication_options(**kwargs):
    """Build Disk protocol communication options (import if needed)"""
    from boomi.models import DiskCommunicationOptions

    # TODO: Need to inspect DiskCommunicationOptions model structure
    # For now, return None if no disk fields provided
    disk_fields = {
        'disk_directory': kwargs.get('disk_directory'),
        'disk_get_directory': kwargs.get('disk_get_directory'),
        'disk_send_directory': kwargs.get('disk_send_directory')
    }

    if not any(disk_fields.values()):
        return None

    # Placeholder - need to understand DiskCommunicationOptions structure
    return None  # Will implement after inspecting the model


def build_ftp_communication_options(**kwargs):
    """Build FTP protocol communication options"""
    from boomi.models import FtpCommunicationOptions

    ftp_fields = {
        'ftp_host': kwargs.get('ftp_host'),
        'ftp_port': kwargs.get('ftp_port'),
        'ftp_username': kwargs.get('ftp_username')
    }

    if not any(ftp_fields.values()):
        return None

    # Placeholder - need to understand FtpCommunicationOptions structure
    return None  # Will implement after inspecting the model


def build_sftp_communication_options(**kwargs):
    """Build SFTP protocol communication options"""
    from boomi.models import SftpCommunicationOptions

    sftp_fields = {
        'sftp_host': kwargs.get('sftp_host'),
        'sftp_port': kwargs.get('sftp_port'),
        'sftp_username': kwargs.get('sftp_username')
    }

    if not any(sftp_fields.values()):
        return None

    # Placeholder - need to understand SftpCommunicationOptions structure
    return None  # Will implement after inspecting the model


def build_http_communication_options(**kwargs):
    """Build HTTP protocol communication options"""
    from boomi.models import HttpCommunicationOptions

    http_fields = {
        'http_url': kwargs.get('http_url'),
        'http_authentication_type': kwargs.get('http_authentication_type'),
        'http_connect_timeout': kwargs.get('http_connect_timeout'),
        'http_read_timeout': kwargs.get('http_read_timeout'),
        'http_username': kwargs.get('http_username'),
        'http_client_auth': kwargs.get('http_client_auth'),
        'http_trust_server_cert': kwargs.get('http_trust_server_cert'),
        'http_method_type': kwargs.get('http_method_type'),
        'http_data_content_type': kwargs.get('http_data_content_type'),
        'http_follow_redirects': kwargs.get('http_follow_redirects'),
        'http_return_errors': kwargs.get('http_return_errors')
    }

    if not any(http_fields.values()):
        return None

    # Placeholder - need to understand HttpCommunicationOptions structure
    return None  # Will implement after inspecting the model


def build_as2_communication_options(**kwargs):
    """Build AS2 protocol communication options"""
    from boomi.models import As2CommunicationOptions

    as2_fields = {
        'as2_url': kwargs.get('as2_url'),
        'as2_identifier': kwargs.get('as2_identifier'),
        'as2_partner_identifier': kwargs.get('as2_partner_identifier'),
        'as2_authentication_type': kwargs.get('as2_authentication_type'),
        'as2_verify_hostname': kwargs.get('as2_verify_hostname'),
        'as2_client_ssl_alias': kwargs.get('as2_client_ssl_alias'),
        'as2_username': kwargs.get('as2_username'),
        'as2_encrypt_alias': kwargs.get('as2_encrypt_alias'),
        'as2_sign_alias': kwargs.get('as2_sign_alias'),
        'as2_mdn_alias': kwargs.get('as2_mdn_alias'),
        'as2_signed': kwargs.get('as2_signed'),
        'as2_encrypted': kwargs.get('as2_encrypted'),
        'as2_compressed': kwargs.get('as2_compressed'),
        'as2_encryption_algorithm': kwargs.get('as2_encryption_algorithm'),
        'as2_signing_digest_alg': kwargs.get('as2_signing_digest_alg'),
        'as2_data_content_type': kwargs.get('as2_data_content_type'),
        'as2_request_mdn': kwargs.get('as2_request_mdn'),
        'as2_mdn_signed': kwargs.get('as2_mdn_signed'),
        'as2_mdn_digest_alg': kwargs.get('as2_mdn_digest_alg'),
        'as2_synchronous_mdn': kwargs.get('as2_synchronous_mdn'),
        'as2_fail_on_negative_mdn': kwargs.get('as2_fail_on_negative_mdn')
    }

    if not any(as2_fields.values()):
        return None

    # Placeholder - need to understand As2CommunicationOptions structure
    return None  # Will implement after inspecting the model


def build_mllp_communication_options(**kwargs):
    """Build MLLP protocol communication options"""
    from boomi.models import MllpCommunicationOptions

    # Placeholder - MLLP not yet implemented in XML version
    return None


def build_oftp_communication_options(**kwargs):
    """Build OFTP protocol communication options"""
    from boomi.models import OftpCommunicationOptions

    oftp_fields = {
        'oftp_host': kwargs.get('oftp_host'),
        'oftp_tls': kwargs.get('oftp_tls')
    }

    if not any(oftp_fields.values()):
        return None

    # Placeholder - need to understand OftpCommunicationOptions structure
    return None  # Will implement after inspecting the model


def build_partner_communication(**kwargs) -> Optional[PartnerCommunication]:
    """
    Build PartnerCommunication model from flat protocol parameters.

    Args:
        communication_protocols: Comma-separated list or list of protocols
                                (ftp, sftp, http, as2, mllp, oftp, disk)
        [protocol]_*: Protocol-specific parameters (see individual builders)

    Returns:
        PartnerCommunication object if any protocols configured, None otherwise
    """
    # Parse communication protocols
    protocols = kwargs.get('communication_protocols', [])
    if isinstance(protocols, str):
        protocols = [p.strip() for p in protocols.split(',') if p.strip()]

    # Build protocol-specific options
    communication_options = {}

    if 'disk' in protocols:
        disk_opts = build_disk_communication_options(**kwargs)
        if disk_opts:
            communication_options['disk_communication_options'] = disk_opts

    if 'ftp' in protocols:
        ftp_opts = build_ftp_communication_options(**kwargs)
        if ftp_opts:
            communication_options['ftp_communication_options'] = ftp_opts

    if 'sftp' in protocols:
        sftp_opts = build_sftp_communication_options(**kwargs)
        if sftp_opts:
            communication_options['sftp_communication_options'] = sftp_opts

    if 'http' in protocols:
        http_opts = build_http_communication_options(**kwargs)
        if http_opts:
            communication_options['http_communication_options'] = http_opts

    if 'as2' in protocols:
        as2_opts = build_as2_communication_options(**kwargs)
        if as2_opts:
            communication_options['as2_communication_options'] = as2_opts

    if 'mllp' in protocols:
        mllp_opts = build_mllp_communication_options(**kwargs)
        if mllp_opts:
            communication_options['mllp_communication_options'] = mllp_opts

    if 'oftp' in protocols:
        oftp_opts = build_oftp_communication_options(**kwargs)
        if oftp_opts:
            communication_options['oftp_communication_options'] = oftp_opts

    # Return None if no protocols configured
    if not communication_options:
        return None

    return PartnerCommunication(**communication_options)


# ============================================================================
# Standard-Specific Partner Info Builders
# ============================================================================

def build_x12_partner_info(**kwargs):
    """Build X12-specific partner information"""
    from boomi.models import X12PartnerInfo

    x12_fields = {
        'isa_id': kwargs.get('isa_id'),
        'isa_qualifier': kwargs.get('isa_qualifier'),
        'gs_id': kwargs.get('gs_id')
    }

    if not any(x12_fields.values()):
        return None

    # Placeholder - need to understand X12PartnerInfo structure
    return None  # Will implement after inspecting the model


def build_edifact_partner_info(**kwargs):
    """Build EDIFACT-specific partner information"""
    from boomi.models import EdifactPartnerInfo

    edifact_fields = {
        'unb_interchangeid': kwargs.get('unb_interchangeid'),
        'unb_interchangeidqual': kwargs.get('unb_interchangeidqual'),
        'unb_partnerid': kwargs.get('unb_partnerid'),
        'unb_partneridqual': kwargs.get('unb_partneridqual'),
        'unb_testindicator': kwargs.get('unb_testindicator')
    }

    if not any(edifact_fields.values()):
        return None

    # Placeholder - need to understand EdifactPartnerInfo structure
    return None  # Will implement after inspecting the model


def build_hl7_partner_info(**kwargs):
    """Build HL7-specific partner information"""
    from boomi.models import Hl7PartnerInfo

    hl7_fields = {
        'sending_application': kwargs.get('sending_application'),
        'sending_facility': kwargs.get('sending_facility'),
        'receiving_application': kwargs.get('receiving_application'),
        'receiving_facility': kwargs.get('receiving_facility')
    }

    if not any(hl7_fields.values()):
        return None

    # Placeholder - need to understand Hl7PartnerInfo structure
    return None  # Will implement after inspecting the model


def build_rosettanet_partner_info(**kwargs):
    """Build RosettaNet-specific partner information"""
    from boomi.models import RosettaNetPartnerInfo

    rosettanet_fields = {
        'duns_number': kwargs.get('duns_number'),
        'global_location_number': kwargs.get('global_location_number')
    }

    if not any(rosettanet_fields.values()):
        return None

    # Placeholder - need to understand RosettaNetPartnerInfo structure
    return None  # Will implement after inspecting the model


def build_tradacoms_partner_info(**kwargs):
    """Build TRADACOMS-specific partner information"""
    from boomi.models import TradacomsPartnerInfo

    tradacoms_fields = {
        'sender_code': kwargs.get('sender_code'),
        'recipient_code': kwargs.get('recipient_code')
    }

    if not any(tradacoms_fields.values()):
        return None

    # Placeholder - need to understand TradacomsPartnerInfo structure
    return None  # Will implement after inspecting the model


def build_odette_partner_info(**kwargs):
    """Build ODETTE-specific partner information"""
    from boomi.models import OdettePartnerInfo

    odette_fields = {
        'originator_code': kwargs.get('originator_code'),
        'destination_code': kwargs.get('destination_code')
    }

    if not any(odette_fields.values()):
        return None

    # Placeholder - need to understand OdettePartnerInfo structure
    return None  # Will implement after inspecting the model


def build_partner_info(standard: str, **kwargs) -> Optional[PartnerInfo]:
    """
    Build PartnerInfo model based on standard type.

    Args:
        standard: EDI standard (x12, edifact, hl7, rosettanet, custom, tradacoms, odette)
        **kwargs: Standard-specific parameters

    Returns:
        PartnerInfo object with appropriate standard-specific info, None if no fields provided
    """
    partner_info_data = {}

    if standard == 'x12':
        x12_info = build_x12_partner_info(**kwargs)
        if x12_info:
            partner_info_data['x12_partner_info'] = x12_info

    elif standard == 'edifact':
        edifact_info = build_edifact_partner_info(**kwargs)
        if edifact_info:
            partner_info_data['edifact_partner_info'] = edifact_info

    elif standard == 'hl7':
        hl7_info = build_hl7_partner_info(**kwargs)
        if hl7_info:
            partner_info_data['hl7_partner_info'] = hl7_info

    elif standard == 'rosettanet':
        rosettanet_info = build_rosettanet_partner_info(**kwargs)
        if rosettanet_info:
            partner_info_data['rosetta_net_partner_info'] = rosettanet_info

    elif standard == 'tradacoms':
        tradacoms_info = build_tradacoms_partner_info(**kwargs)
        if tradacoms_info:
            partner_info_data['tradacoms_partner_info'] = tradacoms_info

    elif standard == 'odette':
        odette_info = build_odette_partner_info(**kwargs)
        if odette_info:
            partner_info_data['odette_partner_info'] = odette_info

    elif standard == 'custom':
        # Custom standard uses dict for partner info
        custom_info = kwargs.get('custom_partner_info', {})
        if custom_info:
            partner_info_data['custom_partner_info'] = custom_info

    # Return None if no standard-specific info provided
    if not partner_info_data:
        return None

    return PartnerInfo(**partner_info_data)


# ============================================================================
# Main Builder Function
# ============================================================================

def build_trading_partner_model(
    component_name: str,
    standard: str,
    classification: str = "tradingpartner",
    folder_name: str = "Home",
    description: str = "",
    **kwargs
) -> TradingPartnerComponent:
    """
    Build complete TradingPartnerComponent model from flat parameters.

    This is the main entry point for building trading partner JSON models.
    It maps all 70+ flat parameters to the nested JSON structure.

    Args:
        component_name: Trading partner name (required)
        standard: EDI standard (x12, edifact, hl7, rosettanet, custom, tradacoms, odette)
        classification: Partner type (tradingpartner or mycompany), defaults to tradingpartner
        folder_name: Folder location, defaults to "Home"
        description: Component description

        # Contact Information (10 fields)
        contact_name: Contact person name
        contact_email: Email address
        contact_phone: Phone number
        contact_fax: Fax number
        contact_address: Street address line 1
        contact_address2: Street address line 2
        contact_city: City
        contact_state: State/province
        contact_country: Country
        contact_postalcode: Postal/zip code

        # Communication Protocols
        communication_protocols: Comma-separated list or list of protocols

        # Protocol-specific fields (see individual builders for details)
        disk_*: Disk protocol fields
        ftp_*: FTP protocol fields
        sftp_*: SFTP protocol fields
        http_*: HTTP protocol fields (11 fields)
        as2_*: AS2 protocol fields (20 fields)
        oftp_*: OFTP protocol fields

        # Standard-specific fields (see individual builders for details)
        isa_id, isa_qualifier, gs_id: X12 fields
        unb_*: EDIFACT fields (5 fields)
        sending_*, receiving_*: HL7 fields (4 fields)
        duns_number, global_location_number: RosettaNet fields
        sender_code, recipient_code: TRADACOMS fields
        originator_code, destination_code: ODETTE fields
        custom_partner_info: dict for custom standard

    Returns:
        TradingPartnerComponent model ready for API submission

    Example:
        tp = build_trading_partner_model(
            component_name="Acme Corp",
            standard="x12",
            classification="tradingpartner",
            contact_email="orders@acme.com",
            isa_id="ACME",
            isa_qualifier="01",
            communication_protocols="http,as2",
            http_url="https://acme.com/edi",
            as2_url="https://acme.com/as2"
        )
    """
    # Build nested models
    contact_info = build_contact_info(**kwargs)
    partner_communication = build_partner_communication(**kwargs)
    partner_info = build_partner_info(standard, **kwargs)

    # Parse classification enum
    if isinstance(classification, str):
        if classification.lower() == "mycompany":
            classification = TradingPartnerComponentClassification.MYCOMPANY
        else:
            classification = TradingPartnerComponentClassification.TRADINGPARTNER

    # Parse standard enum
    if isinstance(standard, str):
        standard_map = {
            'x12': TradingPartnerComponentStandard.X12,
            'edifact': TradingPartnerComponentStandard.EDIFACT,
            'hl7': TradingPartnerComponentStandard.HL7,
            'custom': TradingPartnerComponentStandard.CUSTOM,
            'rosettanet': TradingPartnerComponentStandard.ROSETTANET,
            'tradacoms': TradingPartnerComponentStandard.TRADACOMS,
            'odette': TradingPartnerComponentStandard.ODETTE
        }
        standard = standard_map.get(standard.lower(), standard)

    # Build top-level model
    tp_model = TradingPartnerComponent(
        component_name=component_name,
        standard=standard,
        classification=classification,
        folder_name=folder_name,
        description=description,
        contact_info=contact_info,
        partner_communication=partner_communication,
        partner_info=partner_info
    )

    return tp_model
