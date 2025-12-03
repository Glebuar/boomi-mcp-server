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
    """Build Disk protocol communication options.

    Args:
        disk_get_directory: Directory to read files from
        disk_send_directory: Directory to write files to
        disk_file_filter: File filter pattern (default: *)
    """
    from boomi.models import DiskCommunicationOptions, DiskGetOptions, DiskSendOptions

    get_dir = kwargs.get('disk_get_directory')
    send_dir = kwargs.get('disk_send_directory')
    file_filter = kwargs.get('disk_file_filter', '*')

    if not get_dir and not send_dir:
        return None

    disk_get_options = None
    disk_send_options = None

    if get_dir:
        disk_get_options = DiskGetOptions(
            file_filter=file_filter,
            get_directory=get_dir
        )

    if send_dir:
        disk_send_options = DiskSendOptions(
            send_directory=send_dir
        )

    return DiskCommunicationOptions(
        disk_get_options=disk_get_options,
        disk_send_options=disk_send_options
    )


def build_ftp_communication_options(**kwargs):
    """Build FTP protocol communication options.

    Args:
        ftp_host: FTP server hostname
        ftp_port: FTP server port (default: 21)
        ftp_username: FTP username
        ftp_password: FTP password
        ftp_remote_directory: Remote directory path
    """
    from boomi.models import (
        FtpCommunicationOptions, FtpSettings, FtpGetOptions, FtpSendOptions,
        FtpsslOptions, PrivateCertificate
    )

    host = kwargs.get('ftp_host')
    if not host:
        return None

    port = int(kwargs.get('ftp_port', 21))
    username = kwargs.get('ftp_username', '')
    password = kwargs.get('ftp_password', '')
    remote_dir = kwargs.get('ftp_remote_directory', '/')

    # Build required nested objects
    ssl_options = FtpsslOptions(
        client_ssl_certificate=PrivateCertificate()
    )

    ftp_settings = FtpSettings(
        ftpssl_options=ssl_options,
        host=host,
        port=port,
        user=username,
        password=password
    )

    ftp_get_options = FtpGetOptions(
        file_to_move='*',
        max_file_count=0,
        remote_directory=remote_dir
    )

    ftp_send_options = FtpSendOptions(
        move_to_directory='',
        remote_directory=remote_dir
    )

    return FtpCommunicationOptions(
        ftp_settings=ftp_settings,
        ftp_get_options=ftp_get_options,
        ftp_send_options=ftp_send_options
    )


def build_sftp_communication_options(**kwargs):
    """Build SFTP protocol communication options.

    Args:
        sftp_host: SFTP server hostname
        sftp_port: SFTP server port (default: 22)
        sftp_username: SFTP username
        sftp_password: SFTP password
        sftp_remote_directory: Remote directory path
    """
    from boomi.models import (
        SftpCommunicationOptions, SftpSettings, SftpGetOptions, SftpSendOptions,
        SftpsshOptions, SftpProxySettings
    )

    host = kwargs.get('sftp_host')
    if not host:
        return None

    port = int(kwargs.get('sftp_port', 22))
    username = kwargs.get('sftp_username', '')
    password = kwargs.get('sftp_password', '')
    remote_dir = kwargs.get('sftp_remote_directory', '/')

    # Build required nested objects
    ssh_options = SftpsshOptions(
        known_host_entry='',
        sshkeypassword='',
        sshkeypath=''
    )

    proxy_settings = SftpProxySettings(
        host='',
        password='',
        port=0,
        user=''
    )

    sftp_settings = SftpSettings(
        sftpssh_options=ssh_options,
        sftp_proxy_settings=proxy_settings,
        host=host,
        port=port,
        user=username,
        password=password
    )

    sftp_get_options = SftpGetOptions(
        file_to_move='*',
        max_file_count=0,
        move_to_directory='',
        remote_directory=remote_dir
    )

    sftp_send_options = SftpSendOptions(
        move_to_directory='',
        remote_directory=remote_dir
    )

    return SftpCommunicationOptions(
        sftp_settings=sftp_settings,
        sftp_get_options=sftp_get_options,
        sftp_send_options=sftp_send_options
    )


def build_http_communication_options(**kwargs):
    """Build HTTP protocol communication options.

    Args:
        http_url: HTTP endpoint URL
        http_username: HTTP username (for basic auth)
        http_password: HTTP password (for basic auth)
        http_connect_timeout: Connection timeout in ms
        http_read_timeout: Read timeout in ms
    """
    from boomi.models import (
        HttpCommunicationOptions, HttpSettings, HttpSendOptions,
        HttpAuthSettings, HttpsslOptions, HttpPathElements,
        HttpRequestHeaders, HttpResponseHeaderMapping
    )

    url = kwargs.get('http_url')
    if not url:
        return None

    username = kwargs.get('http_username', '')
    password = kwargs.get('http_password', '')
    connect_timeout = int(kwargs.get('http_connect_timeout', 60000))
    read_timeout = int(kwargs.get('http_read_timeout', 60000))

    # Build required nested objects
    auth_settings = HttpAuthSettings(
        user=username,
        password=password
    )

    ssl_options = HttpsslOptions()

    http_settings = HttpSettings(
        http_auth_settings=auth_settings,
        httpssl_options=ssl_options,
        url=url,
        connect_timeout=connect_timeout,
        read_timeout=read_timeout
    )

    http_send_options = HttpSendOptions(
        path_elements=HttpPathElements(),
        request_headers=HttpRequestHeaders(),
        response_header_mapping=HttpResponseHeaderMapping()
    )

    return HttpCommunicationOptions(
        http_settings=http_settings,
        http_send_options=http_send_options
    )


def build_as2_communication_options(**kwargs):
    """Build AS2 protocol communication options.

    Args:
        as2_url: AS2 endpoint URL
        as2_identifier: Your AS2 identifier
        as2_partner_identifier: Partner's AS2 identifier
        as2_username: Username for basic auth
        as2_password: Password for basic auth
    """
    from boomi.models import (
        As2CommunicationOptions, As2SendSettings, As2SendOptions,
        As2BasicAuthInfo, As2MdnOptions, As2MessageOptions, As2PartnerInfo,
        PrivateCertificate, PublicCertificate
    )

    url = kwargs.get('as2_url')
    if not url:
        return None

    username = kwargs.get('as2_username', '')
    password = kwargs.get('as2_password', '')
    partner_id = kwargs.get('as2_partner_identifier', '')

    # Build required nested objects
    auth_settings = As2BasicAuthInfo(
        user=username,
        password=password
    )

    as2_send_settings = As2SendSettings(
        client_ssl_certificate=PrivateCertificate(),
        ssl_certificate=PublicCertificate(),
        url=url,
        auth_settings=auth_settings
    )

    mdn_options = As2MdnOptions(
        external_url='',
        mdn_client_ssl_cert=PrivateCertificate(),
        mdn_ssl_cert=PublicCertificate()
    )

    message_options = As2MessageOptions(
        subject='AS2 Message'
    )

    as2_send_options = As2SendOptions(
        as2_mdn_options=mdn_options,
        as2_message_options=message_options
    )

    return As2CommunicationOptions(
        as2_send_settings=as2_send_settings,
        as2_send_options=as2_send_options
    )


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
    """Build X12-specific partner information

    Maps user-friendly parameters to nested X12PartnerInfo structure:
    - isa_id → IsaControlInfo.interchange_id
    - isa_qualifier → IsaControlInfo.interchange_id_qualifier
    - gs_id → GsControlInfo.applicationcode
    """
    from boomi.models import X12PartnerInfo, X12ControlInfo, IsaControlInfo, GsControlInfo

    isa_id = kwargs.get('isa_id')
    isa_qualifier = kwargs.get('isa_qualifier')
    gs_id = kwargs.get('gs_id')

    if not any([isa_id, isa_qualifier, gs_id]):
        return None

    # Auto-format qualifier if user provides short form (e.g., 'ZZ' -> 'X12IDQUAL_ZZ')
    if isa_qualifier and not isa_qualifier.startswith('X12IDQUAL_'):
        isa_qualifier = f'X12IDQUAL_{isa_qualifier}'

    # Build ISA control info if we have ISA fields
    isa_control_info = None
    if isa_id or isa_qualifier:
        isa_kwargs = {}
        if isa_id:
            isa_kwargs['interchange_id'] = isa_id
        if isa_qualifier:
            isa_kwargs['interchange_id_qualifier'] = isa_qualifier
        isa_control_info = IsaControlInfo(**isa_kwargs)

    # Build GS control info if we have GS fields
    gs_control_info = None
    if gs_id:
        gs_control_info = GsControlInfo(applicationcode=gs_id)

    # Build X12 control info combining ISA and GS
    x12_control_info = None
    if isa_control_info or gs_control_info:
        control_kwargs = {}
        if isa_control_info:
            control_kwargs['isa_control_info'] = isa_control_info
        if gs_control_info:
            control_kwargs['gs_control_info'] = gs_control_info
        x12_control_info = X12ControlInfo(**control_kwargs)

    # Build and return X12PartnerInfo
    if x12_control_info:
        return X12PartnerInfo(x12_control_info=x12_control_info)

    return None


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
        partner_info=partner_info,
        contact_info=contact_info,
        partner_communication=partner_communication
    )

    return tp_model
