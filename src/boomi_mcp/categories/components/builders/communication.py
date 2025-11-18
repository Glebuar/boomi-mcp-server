"""
Communication protocol XML builders for Boomi components.

These builders generate CommunicationOption XML for various protocols
(AS2, FTP, SFTP, HTTP, etc.). They are reusable across all component
types that support communication protocols.
"""

from typing import Dict, Any, List, Optional
from .base_builder import BaseXMLBuilder


class CommunicationProtocolBuilder(BaseXMLBuilder):
    """Base class for all communication protocol builders."""

    def get_protocol_name(self) -> str:
        """
        Return protocol name (e.g., 'as2', 'ftp', 'http').

        Returns:
            Protocol name in lowercase
        """
        raise NotImplementedError


class AS2ProtocolBuilder(CommunicationProtocolBuilder):
    """AS2 protocol communication builder."""

    def get_protocol_name(self) -> str:
        return "as2"

    def build(self, **params) -> str:
        """
        Build AS2 CommunicationOption XML.

        Args:
            **params: AS2-specific parameters (currently uses defaults)

        Returns:
            AS2 CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="as2">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <AS2Settings url="">
                    <partnerInfo encryptAlias="" mdnAlias="" signAlias=""/>
                    <defaultPartnerSettings authenticationType="NONE" verifyHostname="false">
                      <AuthSettings user=""/>
                    </defaultPartnerSettings>
                  </AS2Settings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <AS2ReceiveAction receiveMethod="PULL">
                      <MessageOptions/>
                    </AS2ReceiveAction>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <AS2SendAction>
                      <MessageOptions compressed="false" dataContentType="application/xml" encrypted="false" encryptionAlgorithm="tripledes" signed="false" signingDigestAlg="SHA1"/>
                      <MDNOptions failOnNegativeMDN="true" mdnDigestAlg="SHA1" requestMDN="false" signed="false" synchronous="true"/>
                    </AS2SendAction>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


class DiskProtocolBuilder(CommunicationProtocolBuilder):
    """Disk protocol communication builder."""

    def get_protocol_name(self) -> str:
        return "disk"

    def build(self, **params) -> str:
        """
        Build Disk CommunicationOption XML.

        Args:
            **params: Disk-specific parameters (currently uses defaults)

        Returns:
            Disk CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="disk">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <DiskSettings directory=""/>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <DiskGetAction getDirectory="" maxFileCount="0"/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <DiskSendAction sendDirectory=""/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


class FTPProtocolBuilder(CommunicationProtocolBuilder):
    """FTP protocol communication builder."""

    def get_protocol_name(self) -> str:
        return "ftp"

    def build(self, **params) -> str:
        """
        Build FTP CommunicationOption XML.

        Args:
            **params: FTP-specific parameters (currently uses defaults)

        Returns:
            FTP CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="ftp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <FTPSettings connectionMode="PASV" host="" port="21">
                    <AuthSettings user=""/>
                    <ProxySettings host="" password="" port="0" proxyEnabled="false" type="ATOM" user=""/>
                    <SSLOptions clientauth="false" trustServerCert="false"/>
                  </FTPSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <FTPGetAction ftpaction="actionget" maxFileCount="0" moveToForceOverride="false"/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <FTPSendAction ftpaction="actionputrename" moveToForceOverride="false"/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


class HTTPProtocolBuilder(CommunicationProtocolBuilder):
    """HTTP/HTTPS protocol communication builder."""

    def get_protocol_name(self) -> str:
        return "http"

    def build(self, **params) -> str:
        """
        Build HTTP CommunicationOption XML.

        Args:
            **params: HTTP-specific parameters (currently uses defaults)

        Returns:
            HTTP CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="http">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <HttpSettings authenticationType="NONE" connectTimeout="15000" readTimeout="60000" url="">
                    <AuthSettings user=""/>
                    <SSLOptions clientauth="false" trustServerCert="false"/>
                  </HttpSettings>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Get" useMyTradingPartnerOptions="false">
                    <HttpGetAction dataContentType="application/xml" followRedirects="false" methodType="GET" returnErrors="false"/>
                    <DataProcessing sequence="post">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <HttpSendAction dataContentType="application/xml" followRedirects="false" methodType="POST" returnErrors="false"/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


class MLLPProtocolBuilder(CommunicationProtocolBuilder):
    """MLLP (Minimal Lower Layer Protocol) communication builder."""

    def get_protocol_name(self) -> str:
        return "mllp"

    def build(self, **params) -> str:
        """
        Build MLLP CommunicationOption XML.

        Args:
            **params: MLLP-specific parameters (currently uses defaults)

        Returns:
            MLLP CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="mllp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <MLLPSettings host="" port="0" timeout="30000"/>
                </SettingsObject>
                <ActionObjects>
                  <ActionObject type="Send" useMyTradingPartnerOptions="false">
                    <MLLPSendAction ackTimeoutMillis="30000" connectTimeoutMillis="30000" sendTimeoutMillis="30000"/>
                    <DataProcessing sequence="pre">
                      <dataprocess/>
                    </DataProcessing>
                  </ActionObject>
                </ActionObjects>
              </CommunicationSettings>
            </CommunicationOption>'''


class OFTPProtocolBuilder(CommunicationProtocolBuilder):
    """ODETTE File Transfer Protocol (OFTP) communication builder."""

    def get_protocol_name(self) -> str:
        return "oftp"

    def build(self, **params) -> str:
        """
        Build OFTP CommunicationOption XML.

        Args:
            **params: OFTP-specific parameters (currently uses defaults)

        Returns:
            OFTP CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="oftp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <OFTPConnectionSettings>
                    <myPartnerInfo/>
                    <defaultOFTPConnectionSettings host="" sfidciph="0" ssidauth="false" tls="false">
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


class SFTPProtocolBuilder(CommunicationProtocolBuilder):
    """SFTP protocol communication builder."""

    def get_protocol_name(self) -> str:
        return "sftp"

    def build(self, **params) -> str:
        """
        Build SFTP CommunicationOption XML.

        Args:
            **params: SFTP-specific parameters (currently uses defaults)

        Returns:
            SFTP CommunicationOption XML string
        """
        return '''            <CommunicationOption commOption="default" method="sftp">
              <CommunicationSettings docType="default">
                <SettingsObject useMyTradingPartnerSettings="false">
                  <SFTPSettings host="" port="22">
                    <AuthSettings user=""/>
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


# Registry of all available protocol builders
PROTOCOL_BUILDERS: Dict[str, type] = {
    "as2": AS2ProtocolBuilder,
    "disk": DiskProtocolBuilder,
    "ftp": FTPProtocolBuilder,
    "http": HTTPProtocolBuilder,
    "mllp": MLLPProtocolBuilder,
    "oftp": OFTPProtocolBuilder,
    "sftp": SFTPProtocolBuilder,
}


def build_communication_xml(protocols: Optional[List[str]] = None, **settings) -> str:
    """
    Build CommunicationOptions XML for multiple protocols.

    This function is reusable across ALL component types that support
    communication protocols (trading partners, processes, etc.).

    Args:
        protocols: List of protocol names (e.g., ['ftp', 'http', 'as2'])
                  If None or empty, returns empty CommunicationOptions
        **settings: Protocol-specific settings (reserved for future use)

    Returns:
        CommunicationOptions XML string

    Example:
        >>> xml = build_communication_xml(['ftp', 'http'])
        >>> # Returns CommunicationOptions with FTP and HTTP configured
    """
    if not protocols:
        return "<CommunicationOptions />"

    options = []
    for protocol_name in protocols:
        protocol_key = protocol_name.lower()
        builder_class = PROTOCOL_BUILDERS.get(protocol_key)

        if builder_class:
            builder = builder_class()
            protocol_settings = settings.get(protocol_name, {})
            options.append(builder.build(**protocol_settings))

    if not options:
        return "<CommunicationOptions />"

    return f'''<CommunicationOptions>
{chr(10).join(options)}
          </CommunicationOptions>'''


def get_supported_protocols() -> List[str]:
    """
    Get list of all supported communication protocols.

    Returns:
        List of protocol names
    """
    return list(PROTOCOL_BUILDERS.keys())
