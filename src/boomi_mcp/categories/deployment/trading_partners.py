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

# Import typed models for query operations
from boomi.models import (
    TradingPartnerComponentQueryConfig,
    TradingPartnerComponentQueryConfigQueryFilter,
    TradingPartnerComponentSimpleExpression,
    TradingPartnerComponentSimpleExpressionOperator,
    TradingPartnerComponentSimpleExpressionProperty
)


# ============================================================================
# Communication Options Helpers (matching UI structure exactly)
# ============================================================================

def build_communication_xml(protocols: list = None) -> str:
    """
    Build PartnerCommunication XML matching UI structure.

    Args:
        protocols: List of protocol names to include (e.g., ['ftp', 'http'])
                  If None or empty, returns empty CommunicationOptions

    Returns:
        XML string for CommunicationOptions section
    """
    if not protocols:
        return "<CommunicationOptions />"

    options = []
    for protocol in protocols:
        proto_lower = protocol.lower()
        if proto_lower == 'as2':
            options.append(_build_as2_option())
        elif proto_lower == 'disk':
            options.append(_build_disk_option())
        elif proto_lower == 'ftp':
            options.append(_build_ftp_option())
        elif proto_lower == 'http':
            options.append(_build_http_option())
        elif proto_lower == 'mllp':
            options.append(_build_mllp_option())
        elif proto_lower == 'oftp':
            options.append(_build_oftp_option())
        elif proto_lower == 'sftp':
            options.append(_build_sftp_option())

    if not options:
        return "<CommunicationOptions />"

    return f'''<CommunicationOptions>
{chr(10).join(options)}
          </CommunicationOptions>'''


def _build_as2_option() -> str:
    """Build AS2 CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="as2">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <AS2ServerSettings useSharedServer="true">
                    <defaultPartnerSettings authenticationType="BASIC" clientsslAlias="" url="" verifyHostname="true">
                      <AuthSettings password="" user=""/>
                    </defaultPartnerSettings>
                  </AS2ServerSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject useMyTradingPartnerOptions="false">
                    <AS2PartnerObject>
                      <partnerInfo as2Id="" encryptAlias="" mdnAlias="" numberOfMessagesToCheckForDuplicates="100000" rejectDuplicateMessageId="false" signAlias="">
                        <ListenAuthSettings/>
                        <ListenAttachmentSettings/>
                      </partnerInfo>
                      <defaultPartnerInfo as2Id="" basicAuthEnabled="false" numberOfMessagesToCheckForDuplicates="100000" rejectDuplicateMessageId="true" useAllowedIpAddresses="false">
                        <ListenAuthSettings/>
                        <ListenAttachmentSettings/>
                      </defaultPartnerInfo>
                      <AS2MessageOptions attachmentOption="BATCH" compressed="false" dataContentType="textplain" enabledFoldedHeaders="false" encrypted="false" encryptionAlgorithm="tripledes" maxDocumentCount="1" multipleAttachments="false" signed="false" signingDigestAlg="SHA1"/>
                      <AS2MDNOptions externalURL="" failOnNegativeMDN="false" mdnDigestAlg="SHA1" requestMDN="false" signed="false" synchronous="sync" useExternalURL="false" useSSL="false"/>
                    </AS2PartnerObject>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


def _build_disk_option() -> str:
    """Build Disk CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="disk">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <DiskSettings directory=""/>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <DiskGetAction deleteAfterRead="false" fileFilter="" filterMatchType="wildcard" getDirectory="" maxFileCount="0"/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <DiskSendAction createDirectory="false" sendDirectory="" writeOption="unique"/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


def _build_ftp_option() -> str:
    """Build FTP CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="ftp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <FTPSettings connectionMode="passive">
                    <AuthSettings/>
                    <SSLOptions clientauth="false" sslmode="none"/>
                  </FTPSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <FTPGetAction ftpaction="actionget" maxFileCount="0" transferType="binary"/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <FTPSendAction ftpaction="actionputrename" transferType="binary"/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


def _build_http_option() -> str:
    """Build HTTP CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="http">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <HttpSettings authenticationType="NONE">
                    <AuthSettings/>
                    <OAuthSettings/>
                    <OAuth2Settings grantType="code">
                      <credentials clientId=""/>
                      <authorizationTokenEndpoint url=""/>
                      <authorizationParameters/>
                      <accessTokenEndpoint url=""/>
                      <accessTokenParameters/>
                      <scope/>
                    </OAuth2Settings>
                    <SSLOptions clientauth="false" trustServerCert="false"/>
                  </HttpSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Listen" useMyTradingPartnerOptions="false">
                    <B2BServerListenAction/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <HttpGetAction dataContentType="text/plain" followRedirects="false" methodType="GET" requestProfileType="NONE" responseProfileType="NONE" returnErrors="false">
                      <requestHeaders/>
                      <pathElements/>
                      <responseHeaderMapping/>
                      <reflectHeaders/>
                    </HttpGetAction>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <HttpSendAction dataContentType="text/plain" followRedirects="false" methodType="POST" requestProfileType="NONE" responseProfileType="NONE" returnErrors="false">
                      <requestHeaders/>
                      <pathElements/>
                      <responseHeaderMapping/>
                      <reflectHeaders/>
                    </HttpSendAction>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


def _build_mllp_option() -> str:
    """Build MLLP CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="mllp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false"/>
                <ActionObjects>
                  <ActionObject useMyTradingPartnerOptions="false">
                    <MLLPPartnerObject>
                      <partnerInfo/>
                    </MLLPPartnerObject>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


def _build_oftp_option() -> str:
    """Build OFTP CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="oftp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <OFTPConnectionSettings>
                    <myPartnerInfo/>
                    <defaultOFTPConnectionSettings sfidciph="0" ssidauth="false" tls="false">
                      <myPartnerInfo/>
                    </defaultOFTPConnectionSettings>
                  </OFTPConnectionSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Listen" useMyTradingPartnerOptions="false">
                    <OFTPServerListenAction>
                      <OFTPPartnerGroup>
                        <myCompanyInfo/>
                        <myPartnerInfo sfidsec-encrypt="false" sfidsec-sign="false" sfidsign="false" ssidcmpr="false"/>
                        <defaultPartnerInfo sfidsec-encrypt="false" sfidsec-sign="false" sfidsign="false" ssidcmpr="false"/>
                      </OFTPPartnerGroup>
                      <OFTPListenOptions operation="LISTEN">
                        <GatewayPartnerGroup>
                          <myPartnerInfo/>
                        </GatewayPartnerGroup>
                      </OFTPListenOptions>
                    </OFTPServerListenAction>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <OFTPGetAction>
                      <OFTPPartnerGroup>
                        <myCompanyInfo/>
                        <myPartnerInfo sfidsec-encrypt="false" sfidsec-sign="false" sfidsign="false" ssidcmpr="false"/>
                        <defaultPartnerInfo sfidsec-encrypt="false" sfidsec-sign="false" sfidsign="false" ssidcmpr="false"/>
                      </OFTPPartnerGroup>
                    </OFTPGetAction>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <OFTPSendAction>
                      <OFTPPartnerGroup>
                        <myCompanyInfo/>
                        <myPartnerInfo sfidsec-encrypt="false" sfidsec-sign="false" sfidsign="false" ssidcmpr="false"/>
                        <defaultPartnerInfo sfidsec-encrypt="false" sfidsec-sign="false" sfidsign="false" ssidcmpr="false"/>
                      </OFTPPartnerGroup>
                      <OFTPSendOptions cd="false" operation="SEND">
                        <defaultPartnerSettings cd="false"/>
                      </OFTPSendOptions>
                    </OFTPSendAction>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


def _build_sftp_option() -> str:
    """Build SFTP CommunicationOption (exact UI structure)"""
    return '''            <CommunicationOption commOption="default" method="sftp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <SFTPSettings>
                    <AuthSettings/>
                    <ProxySettings host="" password="" port="0" proxyEnabled="false" type="ATOM" user=""/>
                    <SSHOptions dhKeySizeMax1024="true" sshkeyauth="false"/>
                  </SFTPSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <SFTPGetAction maxFileCount="0" moveToForceOverride="false" sftpaction="actionget"/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <SFTPSendAction moveToForceOverride="false" sftpaction="actionputrename"/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


# ============================================================================
# XML Template Builders (aligned with boomi-python SDK examples)
# ============================================================================



# ============================================================================
# XML Template Builders (aligned with boomi-python SDK examples)
# ============================================================================

def build_trading_partner_xml_x12(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # X12Options parameters
    acknowledgementoption: str = "donotackitem",
    envelopeoption: str = "groupall",
    file_delimiter: str = "stardelimited",
    filter_acknowledgements: str = "false",
    outbound_interchange_validation: str = "false",
    outbound_validation_option: str = "filterError",
    reject_duplicate_interchange: str = "false",
    segment_char: str = "newline",
    # ISAControlInfo parameters
    isa_ackrequested: str = "false",
    isa_authorinfoqual: str = "00",
    isa_interchangeid: str = "",
    isa_interchangeidqual: str = "01",
    isa_securityinfoqual: str = "00",
    isa_testindicator: str = "P",
    # GSControlInfo parameters
    gs_respagencycode: str = "T",
    # ContactInfo parameters (optional)
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build X12 trading partner component XML.

    This follows the exact structure from the boomi-python SDK example
    for creating X12 trading partner components via the Component API.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification (mytradingpartner, tradingpartner, etc.)

        X12Options parameters:
        - acknowledgementoption: Acknowledgement option (donotackitem, ackall, etc.)
        - envelopeoption: Envelope option (groupall, groupbydocument, etc.)
        - file_delimiter: File delimiter type (stardelimited, etc.)
        - filter_acknowledgements: Filter acknowledgements (true/false)
        - outbound_interchange_validation: Validate outbound interchanges (true/false)
        - outbound_validation_option: Validation option (filterError, rejectAll, etc.)
        - reject_duplicate_interchange: Reject duplicates (true/false)
        - segment_char: Segment character (newline, etc.)

        ISAControlInfo parameters:
        - isa_ackrequested: Acknowledgement requested (true/false)
        - isa_authorinfoqual: Authorization info qualifier
        - isa_interchangeid: ISA interchange ID
        - isa_interchangeidqual: ISA interchange ID qualifier
        - isa_securityinfoqual: Security info qualifier
        - isa_testindicator: Test indicator (P=Production, T=Test)

        GSControlInfo parameters:
        - gs_respagencycode: Responsible agency code

        ContactInfo parameters (all optional):
        - contact_name: Contact person name
        - contact_email: Contact email
        - contact_phone: Contact phone
        - contact_fax: Fax number
        - contact_address: Street address (line 1)
        - contact_address2: Street address (line 2)
        - contact_city: City
        - contact_state: State/province
        - contact_country: Country
        - contact_postalcode: Postal/ZIP code

    Returns:
        XML string for creating the trading partner component
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    # Build Communication XML (empty by default, can be configured later via UI)
    communication_xml = build_communication_xml()

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="x12">
            {contact_info_xml}
            <PartnerInfo>
                <X12PartnerInfo>
                    <X12Options
                        acknowledgementoption="{acknowledgementoption}"
                        envelopeoption="{envelopeoption}"
                        fileDelimiter="{file_delimiter}"
                        filteracknowledgements="{filter_acknowledgements}"
                        outboundInterchangeValidation="{outbound_interchange_validation}"
                        outboundValidationOption="{outbound_validation_option}"
                        rejectDuplicateInterchange="{reject_duplicate_interchange}"
                        segmentchar="{segment_char}" />
                    <X12ControlInfo>
                        <ISAControlInfo
                            ackrequested="{isa_ackrequested}"
                            authorinfoqual="{isa_authorinfoqual}"
                            interchangeid="{isa_interchangeid}"
                            interchangeidqual="{isa_interchangeidqual}"
                            securityinfoqual="{isa_securityinfoqual}"
                            testindicator="{isa_testindicator}" />
                        <GSControlInfo respagencycode="{gs_respagencycode}" />
                    </X12ControlInfo>
                </X12PartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
                <X12PartnerCommunication>
                    {communication_xml}
                </X12PartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml_edifact(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # UNB parameters
    unb_interchangeid: str = "",
    unb_interchangeidqual: str = "14",
    unb_partnerid: str = "",
    unb_partneridqual: str = "14",
    unb_testindicator: str = "1",
    # ContactInfo parameters
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build EDIFACT trading partner component XML.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification
        unb_interchangeid: UNB interchange ID
        unb_interchangeidqual: UNB interchange ID qualifier
        unb_partnerid: UNB partner ID
        unb_partneridqual: UNB partner ID qualifier
        unb_testindicator: Test indicator (1=Production, others for test)
        contact_*: Optional contact information fields

    Returns:
        XML string for creating EDIFACT trading partner
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="edifact">
            {contact_info_xml}
            <PartnerInfo>
                <EdifactPartnerInfo>
                    <EdifactOptions
                        acknowledgementoption="donotackitem"
                        compositeDelimiter="colondelimited"
                        envelopeoption="groupall"
                        fileDelimiter="plusdelimited"
                        filteracknowledgements="false"
                        includeUNA="false"
                        outboundValidationOption="filterError"
                        rejectDuplicateInterchange="false"
                        segmentchar="singlequote" />
                    <EdifactControlInfo>
                        <UNBControlInfo
                            ackRequest="false"
                            interchangeIdQual="NA"
                            priority="NA"
                            refPassQual="NA"
                            syntaxId="UNOA"
                            syntaxVersion="1"
                            testIndicator="NA" />
                        <UNGControlInfo
                            applicationIdQual="NA"
                            useFunctionalGroups="false" />
                        <UNHControlInfo
                            controllingAgency="UN"
                            release="09B"
                            version="D" />
                    </EdifactControlInfo>
                </EdifactPartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
                <EdifactPartnerCommunication>
                    <CommunicationOptions />
                </EdifactPartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml_hl7(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # HL7 parameters
    sending_application: str = "",
    sending_facility: str = "",
    receiving_application: str = "",
    receiving_facility: str = "",
    # ContactInfo parameters
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build HL7 trading partner component XML.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification
        sending_application: MSH-3 Sending Application
        sending_facility: MSH-4 Sending Facility
        receiving_application: MSH-5 Receiving Application
        receiving_facility: MSH-6 Receiving Facility
        contact_*: Optional contact information fields

    Returns:
        XML string for creating HL7 trading partner
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="hl7">
            {contact_info_xml}
            <PartnerInfo>
                <HL7PartnerInfo>
                    <HL7Options
                        acceptackoption="NE"
                        batchoption="none"
                        compositeDelimiter="caratdelimited"
                        fileDelimiter="bardelimited"
                        filteracknowledgements="false"
                        outboundValidationOption="filterError"
                        segmentchar="carriagereturn"
                        subCompositeDelimiter="ampersanddelimited" />
                    <HL7ControlInfo>
                        <MSHControlInfo
                            alternateCharSetHandlingScheme=""
                            characterSet=""
                            countryCode="">
                            <Application />
                            <Facility />
                            <ProcessingId processingId="P" processingMode="NOT_PRESENT" />
                            <VersionId versionId="v26">
                                <InternationalizationCode />
                                <InternationalizationVersionId />
                            </VersionId>
                            <PrincipalLanguage />
                            <MessageProfileIdentifier />
                            <ResponsibleOrg>
                                <OrgNameTypeCode />
                                <AssigningAuthority />
                                <AssigningFacility />
                            </ResponsibleOrg>
                            <NetworkAddress />
                        </MSHControlInfo>
                    </HL7ControlInfo>
                </HL7PartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
                <HL7PartnerCommunication>
                    <CommunicationOptions />
                </HL7PartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml_rosettanet(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # RosettaNet parameters
    duns_number: str = "",
    global_location_number: str = "",
    # ContactInfo parameters
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build RosettaNet trading partner component XML.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification
        duns_number: DUNS number for the partner
        global_location_number: GLN (Global Location Number)
        contact_*: Optional contact information fields

    Returns:
        XML string for creating RosettaNet trading partner
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="rosettanet">
            {contact_info_xml}
            <PartnerInfo>
                <RosettaNetPartnerInfo>
                    <RosettaNetOptions
                        filtersignals="false"
                        outboundDocumentValidation="false"
                        rejectDuplicateTransactionId="false"
                        version="v20" />
                    <RosettaNetControlInfo
                        partnerIdType="DUNS"
                        usageCode="Test" />
                    <RosettaNetMessageOptions
                        compressed="false"
                        encryptServiceHeader="false"
                        encrypted="false"
                        encryptionAlgorithm="tripledes"
                        signed="false"
                        signingDigestAlg="SHA1" />
                </RosettaNetPartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
                <RosettaNetPartnerCommunication>
                    <CommunicationOptions />
                </RosettaNetPartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml_custom(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # ContactInfo parameters
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build custom standard trading partner component XML.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification
        contact_*: Optional contact information fields

    Returns:
        XML string for creating custom trading partner
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="edicustom">
            {contact_info_xml}
            <PartnerInfo>
                <CustomPartnerInfo />
            </PartnerInfo>
            <PartnerCommunication>
                <CustomPartnerCommunication>
                    <CommunicationOptions />
                </CustomPartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml_tradacoms(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # TRADACOMS parameters
    sender_code: str = "",
    recipient_code: str = "",
    # ContactInfo parameters
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build TRADACOMS trading partner component XML.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification
        sender_code: TRADACOMS sender code
        recipient_code: TRADACOMS recipient code
        contact_*: Optional contact information fields

    Returns:
        XML string for creating TRADACOMS trading partner
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="tradacoms">
            {contact_info_xml}
            <PartnerInfo>
                <TradacomsPartnerInfo>
                    <TradacomsOptions
                        compositeDelimiter="colondelimited"
                        fileDelimiter="plusdelimited"
                        segmentchar="singlequote" />
                    <TradacomsControlInfo>
                        <STXControlInfo />
                    </TradacomsControlInfo>
                </TradacomsPartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
                <TradacomsPartnerCommunication>
                    <CommunicationOptions />
                </TradacomsPartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml_odette(
    name: str,
    folder_name: str = "Home",
    description: str = "",
    classification: str = "mytradingpartner",
    # ODETTE parameters
    originator_code: str = "",
    destination_code: str = "",
    # ContactInfo parameters
    contact_name: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    contact_address: str = "",
    contact_city: str = "",
    contact_state: str = "",
    contact_country: str = "",
    contact_postalcode: str = ""
) -> str:
    """
    Build ODETTE trading partner component XML.

    Args:
        name: Trading partner component name
        folder_name: Folder to create the component in
        description: Component description
        classification: Partner classification
        originator_code: ODETTE originator code
        destination_code: ODETTE destination code
        contact_*: Optional contact information fields

    Returns:
        XML string for creating ODETTE trading partner
    """
    # Build ContactInfo XML with provided attributes
    contact_attrs = []
    if contact_name:
        contact_attrs.append(f'name="{contact_name}"')
    if contact_email:
        contact_attrs.append(f'email="{contact_email}"')
    if contact_phone:
        contact_attrs.append(f'phone="{contact_phone}"')
    if contact_fax:
        contact_attrs.append(f'fax="{contact_fax}"')
    if contact_address:
        contact_attrs.append(f'address1="{contact_address}"')
    if contact_address2:
        contact_attrs.append(f'address2="{contact_address2}"')
    if contact_city:
        contact_attrs.append(f'city="{contact_city}"')
    if contact_state:
        contact_attrs.append(f'state="{contact_state}"')
    if contact_country:
        contact_attrs.append(f'country="{contact_country}"')
    if contact_postalcode:
        contact_attrs.append(f'postalcode="{contact_postalcode}"')

    if contact_attrs:
        contact_info_xml = f'<ContactInfo {" ".join(contact_attrs)} />'
    else:
        contact_info_xml = "<ContactInfo />"

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               name="{name}"
               type="tradingpartner"
               folderName="{folder_name}">
    <bns:encryptedValues />
    <bns:description>{description}</bns:description>
    <bns:object>
        <TradingPartner classification="{classification}" standard="odette">
            {contact_info_xml}
            <PartnerInfo>
                <OdettePartnerInfo>
                    <OdetteOptions
                        acknowledgementoption="donotackitem"
                        compositeDelimiter="colondelimited"
                        envelopeoption="groupall"
                        fileDelimiter="plusdelimited"
                        filteracknowledgements="false"
                        includeUNA="false"
                        outboundValidationOption="filterError"
                        rejectDuplicateInterchange="false"
                        segmentchar="singlequote" />
                    <OdetteControlInfo>
                        <UNBControlInfo
                            ackRequest="false"
                            interchangeIdQual="NA"
                            priority="NA"
                            refPassQual="NA"
                            syntaxId="UNOA"
                            syntaxVersion="1"
                            testIndicator="NA" />
                        <UNHControlInfo
                            controllingAgency="UN"
                            release="09B"
                            version="D" />
                    </OdetteControlInfo>
                </OdettePartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
                <OdettePartnerCommunication>
                    <CommunicationOptions />
                </OdettePartnerCommunication>
            </PartnerCommunication>
            <DocumentTypes />
            <Archiving />
        </TradingPartner>
    </bns:object>
    <bns:processOverrides />
</bns:Component>'''


def build_trading_partner_xml(request_data: Dict[str, Any]) -> str:
    """
    Main dispatcher function to build trading partner XML based on standard.

    Args:
        request_data: Dictionary containing all trading partner parameters

    Returns:
        XML string for creating the trading partner component

    Raises:
        ValueError: If standard is not supported
    """
    standard = request_data.get("standard", "x12").lower()
    name = request_data.get("component_name")
    folder_name = request_data.get("folder_name", "Home")
    description = request_data.get("description", "Trading partner created via MCP")
    classification = request_data.get("classification", "mytradingpartner").lower()

    # Extract contact info if provided
    contact_info = request_data.get("contact_info", {})
    contact_params = {
        "contact_name": contact_info.get("name", ""),
        "contact_email": contact_info.get("email", ""),
        "contact_phone": contact_info.get("phone", ""),
        "contact_fax": contact_info.get("fax", ""),
        "contact_address": contact_info.get("address", ""),
        "contact_address2": contact_info.get("address2", ""),
        "contact_city": contact_info.get("city", ""),
        "contact_state": contact_info.get("state", ""),
        "contact_country": contact_info.get("country", ""),
        "contact_postalcode": contact_info.get("postal_code", "")
    }

    # Route to appropriate builder based on standard
    if standard == "x12":
        partner_info = request_data.get("partner_info", {})
        x12_options = request_data.get("x12_options", {})

        return build_trading_partner_xml_x12(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            # X12Options
            acknowledgementoption=x12_options.get("acknowledgementoption", "donotackitem"),
            envelopeoption=x12_options.get("envelopeoption", "groupall"),
            file_delimiter=x12_options.get("file_delimiter", "stardelimited"),
            filter_acknowledgements=x12_options.get("filter_acknowledgements", "false"),
            outbound_interchange_validation=x12_options.get("outbound_interchange_validation", "false"),
            outbound_validation_option=x12_options.get("outbound_validation_option", "filterError"),
            reject_duplicate_interchange=x12_options.get("reject_duplicate_interchange", "false"),
            segment_char=x12_options.get("segment_char", "newline"),
            # ISAControlInfo
            isa_ackrequested=partner_info.get("isa_ackrequested", "false"),
            isa_authorinfoqual=partner_info.get("isa_authorinfoqual", "00"),
            isa_interchangeid=partner_info.get("isa_id", ""),
            isa_interchangeidqual=partner_info.get("isa_qualifier", "01"),
            isa_securityinfoqual=partner_info.get("isa_securityinfoqual", "00"),
            isa_testindicator=partner_info.get("isa_testindicator", "P"),
            # GSControlInfo
            gs_respagencycode=partner_info.get("gs_respagencycode", "T"),
            # ContactInfo
            **contact_params
        )

    elif standard == "edifact":
        partner_info = request_data.get("partner_info", {})
        return build_trading_partner_xml_edifact(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            unb_interchangeid=partner_info.get("unb_id", ""),
            unb_interchangeidqual=partner_info.get("unb_qualifier", "14"),
            unb_partnerid=partner_info.get("unb_partner_id", ""),
            unb_partneridqual=partner_info.get("unb_partner_qualifier", "14"),
            unb_testindicator=partner_info.get("unb_testindicator", "1"),
            **contact_params
        )

    elif standard == "hl7":
        partner_info = request_data.get("partner_info", {})
        return build_trading_partner_xml_hl7(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            sending_application=partner_info.get("sending_application", ""),
            sending_facility=partner_info.get("sending_facility", ""),
            receiving_application=partner_info.get("receiving_application", ""),
            receiving_facility=partner_info.get("receiving_facility", ""),
            **contact_params
        )

    elif standard == "rosettanet":
        partner_info = request_data.get("partner_info", {})
        return build_trading_partner_xml_rosettanet(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            duns_number=partner_info.get("duns", ""),
            global_location_number=partner_info.get("gln", ""),
            **contact_params
        )

    elif standard == "custom":
        return build_trading_partner_xml_custom(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            **contact_params
        )

    elif standard == "tradacoms":
        partner_info = request_data.get("partner_info", {})
        return build_trading_partner_xml_tradacoms(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            sender_code=partner_info.get("sender_code", ""),
            recipient_code=partner_info.get("recipient_code", ""),
            **contact_params
        )

    elif standard == "odette":
        partner_info = request_data.get("partner_info", {})
        return build_trading_partner_xml_odette(
            name=name,
            folder_name=folder_name,
            description=description,
            classification=classification,
            originator_code=partner_info.get("originator_code", ""),
            destination_code=partner_info.get("destination_code", ""),
            **contact_params
        )

    else:
        raise ValueError(f"Unsupported trading partner standard: {standard}. Supported: x12, edifact, hl7, rosettanet, custom, tradacoms, odette")


# ============================================================================
# Trading Partner CRUD Operations
# ============================================================================

def create_trading_partner(boomi_client, profile: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new trading partner component in Boomi using XML-based Component API.

    This implementation follows the boomi-python SDK example pattern of using
    the generic Component API with XML request bodies instead of the specialized
    trading_partner_component API.

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        request_data: Trading partner configuration including:
            - component_name: Name of the trading partner (required)
            - standard: Trading standard - x12, edifact, hl7, rosettanet, custom, tradacoms, or odette (default: x12)
            - classification: Classification type (default: mytradingpartner)
            - folder_name: Folder name (default: Home)
            - description: Component description (optional)
            - contact_info: Optional contact information dict with: name, email, phone, address, city, state, country, postal_code
            - partner_info: Partner-specific information dict (standard-dependent):
                - X12: isa_id, isa_qualifier, isa_ackrequested, isa_authorinfoqual, isa_securityinfoqual, isa_testindicator, gs_respagencycode
                - EDIFACT: unb_id, unb_qualifier, unb_partner_id, unb_partner_qualifier, unb_testindicator
                - HL7: sending_application, sending_facility, receiving_application, receiving_facility
                - RosettaNet: duns, gln
            - x12_options: X12-specific options dict (for X12 only):
                - acknowledgementoption, envelopeoption, file_delimiter, filter_acknowledgements,
                  outbound_interchange_validation, outbound_validation_option, reject_duplicate_interchange, segment_char

    Returns:
        Created trading partner details or error

    Example:
        request_data = {
            "component_name": "My Trading Partner",
            "standard": "x12",
            "classification": "mytradingpartner",
            "folder_name": "Home",
            "partner_info": {
                "isa_id": "MYPARTNER",
                "isa_qualifier": "01"
            }
        }
    """
    try:
        # Validate required fields
        if not request_data.get("component_name"):
            return {
                "_success": False,
                "error": "component_name is required",
                "message": "Trading partner name (component_name) is required"
            }

        # Build XML using the appropriate template builder
        try:
            xml_body = build_trading_partner_xml(request_data)
        except ValueError as ve:
            return {
                "_success": False,
                "error": str(ve),
                "message": f"Invalid trading partner configuration: {str(ve)}"
            }

        # Create trading partner using Component API (not trading_partner_component API)
        # This matches the SDK example approach
        result = boomi_client.component.create_component(request_body=xml_body)

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
                "classification": request_data.get("classification", "mytradingpartner"),
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
        # If ContactInfo parsing fails, fall back to Component API
        used_component_api = False
        try:
            result = boomi_client.trading_partner_component.get_trading_partner_component(
                id_=component_id
            )
        except Exception as sdk_error:
            # If SDK ContactInfo parsing fails, use Component API instead
            if "ContactInfo" in str(sdk_error):
                result = boomi_client.component.get_component(component_id=component_id)
                used_component_api = True
            else:
                raise

        # Extract component ID using SDK pattern (id_ attribute)
        retrieved_id = None
        if hasattr(result, 'id_'):
            retrieved_id = result.id_
        elif hasattr(result, 'id'):
            retrieved_id = result.id
        elif hasattr(result, 'component_id'):
            retrieved_id = result.component_id
        else:
            retrieved_id = component_id

        # If we used Component API, parse XML to extract additional fields
        standard = None
        classification = None
        if used_component_api:
            try:
                xml_str = result.to_xml()
                root = ET.fromstring(xml_str)

                # Extract standard and classification from TradingPartner element
                trading_partner = root.find('.//TradingPartner')
                if trading_partner is not None:
                    standard = trading_partner.get('standard')
                    classification = trading_partner.get('classification')
            except Exception as xml_error:
                # If XML parsing fails, just continue without these fields
                pass

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
        # If we used Component API, parse ContactInfo from XML
        if used_component_api:
            try:
                xml_str = result.to_xml()
                root = ET.fromstring(xml_str)

                # Find ContactInfo element
                contact_elem = root.find('.//ContactInfo')
                if contact_elem is not None:
                    contact_info = {
                        "name": contact_elem.get('name'),
                        "email": contact_elem.get('email'),
                        "phone": contact_elem.get('phone'),
                        "address1": contact_elem.get('address1'),
                        "address2": contact_elem.get('address2'),
                        "city": contact_elem.get('city'),
                        "state": contact_elem.get('state'),
                        "country": contact_elem.get('country'),
                        "postalcode": contact_elem.get('postalcode'),
                        "fax": contact_elem.get('fax')
                    }
                    # Remove None values
                    contact_info = {k: v for k, v in contact_info.items() if v is not None}
            except Exception as xml_error:
                # If XML parsing fails, just continue without contact info
                pass
        else:
            # Use object attributes if available (trading_partner_component API)
            if hasattr(result, 'ContactInfo') or hasattr(result, 'contact_info'):
                contact = getattr(result, 'ContactInfo', None) or getattr(result, 'contact_info', None)
                if contact:
                    # Use safe attribute access with defaults for all fields
                    contact_info = {
                        "name": getattr(contact, 'contact_name', getattr(contact, 'name', None)),
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

        return {
            "_success": True,
            "trading_partner": {
                "component_id": retrieved_id,
                "name": getattr(result, 'name', getattr(result, 'component_name', None)),
                "standard": standard if used_component_api else getattr(result, 'standard', None),
                "classification": classification if used_component_api else getattr(result, 'classification', None),
                "folder_id": getattr(result, 'folder_id', None),
                "folder_name": getattr(result, 'folder_name', None),
                "organization_id": getattr(result, 'organization_id', None),
                "deleted": getattr(result, 'deleted', False),
                "partner_info": partner_info if partner_info else None,
                "contact_info": contact_info if contact_info else None
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
    Update an existing trading partner component using XML-based Component API.

    This implementation follows the boomi-python SDK example pattern:
    1. Get component XML using component.get_component()
    2. Get XML string using component.to_xml()
    3. Parse and modify XML using ElementTree
    4. Update using component.update_component() with modified XML

    Args:
        boomi_client: Authenticated Boomi SDK client
        profile: Profile name for authentication
        component_id: Trading partner component ID to update
        updates: Fields to update (component_name, contact_info, partner_info, etc.)

    Returns:
        Updated trading partner details or error
    """
    try:
        import xml.etree.ElementTree as ET

        # Step 1: Get the existing component using Component API (not trading_partner_component)
        component = boomi_client.component.get_component(component_id=component_id)

        if not component:
            return {
                "_success": False,
                "error": "Component not found",
                "message": f"Trading partner {component_id} not found"
            }

        # Step 2: Get full XML structure using to_xml() method
        try:
            full_xml = component.to_xml()
        except Exception as e:
            return {
                "_success": False,
                "error": f"Failed to get component XML: {str(e)}",
                "message": "Could not retrieve component XML structure"
            }

        # Step 3: Parse and modify the XML
        try:
            root = ET.fromstring(full_xml)

            # Update component name if provided
            if "component_name" in updates:
                root.set('name', updates["component_name"])

            # Update description if provided
            if "description" in updates:
                root.set('description', updates["description"])

            # For contact info and partner info, we need to navigate to the TradingPartner element
            # Find the TradingPartner element in the object section
            ns = {'bns': 'http://api.platform.boomi.com/'}
            trading_partner = root.find('.//TradingPartner')

            if trading_partner is None:
                return {
                    "_success": False,
                    "error": "Not a trading partner component",
                    "message": "Component XML does not contain TradingPartner element"
                }

            # Update contact info if provided
            if "contact_info" in updates:
                contact_info = trading_partner.find('ContactInfo')
                if contact_info is None:
                    contact_info = ET.SubElement(trading_partner, 'ContactInfo')

                # Clear existing contact info
                contact_info.clear()

                # Add updated contact fields (all 10 fields)
                contact = updates["contact_info"]
                if contact.get("name"):
                    contact_info.set('name', contact["name"])
                if contact.get("email"):
                    contact_info.set('email', contact["email"])
                if contact.get("phone"):
                    contact_info.set('phone', contact["phone"])
                if contact.get("fax"):
                    contact_info.set('fax', contact["fax"])
                if contact.get("address"):
                    contact_info.set('address1', contact["address"])
                if contact.get("address2"):
                    contact_info.set('address2', contact["address2"])
                if contact.get("city"):
                    contact_info.set('city', contact["city"])
                if contact.get("state"):
                    contact_info.set('state', contact["state"])
                if contact.get("country"):
                    contact_info.set('country', contact["country"])
                if contact.get("postal_code"):
                    contact_info.set('postalcode', contact["postal_code"])

            # Update partner-specific info (X12, EDIFACT, etc.) if provided
            if "partner_info" in updates:
                partner_info_elem = trading_partner.find('PartnerInfo')
                if partner_info_elem is not None:
                    info = updates["partner_info"]

                    # Update X12 fields
                    x12_elem = partner_info_elem.find('.//X12ControlInfo')
                    if x12_elem is not None:
                        isa_elem = x12_elem.find('ISAControlInfo')
                        if isa_elem is not None:
                            if "isa_id" in info:
                                isa_elem.set('isaid', info["isa_id"])
                            if "isa_qualifier" in info:
                                isa_elem.set('isaqualifier', info["isa_qualifier"])

                        gs_elem = x12_elem.find('GSControlInfo')
                        if gs_elem is not None and "gs_id" in info:
                            gs_elem.set('gsid', info["gs_id"])

                    # Update EDIFACT fields
                    edifact_elem = partner_info_elem.find('.//EDIFACTControlInfo')
                    if edifact_elem is not None:
                        unb_elem = edifact_elem.find('UNBControlInfo')
                        if unb_elem is not None:
                            if "unb_id" in info:
                                unb_elem.set('unbid', info["unb_id"])
                            if "unb_qualifier" in info:
                                unb_elem.set('unbqualifier', info["unb_qualifier"])

            # Convert back to XML string
            modified_xml = ET.tostring(root, encoding='unicode')

        except ET.ParseError as e:
            return {
                "_success": False,
                "error": f"XML parse error: {str(e)}",
                "message": "Failed to parse component XML"
            }

        # Step 4: Update the component with modified XML
        result = boomi_client.component.update_component(
            component_id=component_id,
            request_body=modified_xml
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