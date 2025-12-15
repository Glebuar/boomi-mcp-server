"""
X12 Trading Partner Builder.

Builds XML for X12 EDI trading partner components using the Component API.
"""

from typing import Optional, List
from .base_builder import TradingPartnerBuilder, ComponentXMLWrapper
from .communication import build_communication_xml


class X12TradingPartnerBuilder(TradingPartnerBuilder):
    """
    Builder for X12 EDI trading partner components.

    X12 is a widely used EDI standard in North America for electronic
    business transactions (invoices, purchase orders, shipment notices, etc.).
    """

    def get_standard_name(self) -> str:
        """Return the standard name."""
        return "x12"

    def build(
        self,
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
        contact_fax: str = "",
        contact_address: str = "",
        contact_address2: str = "",
        contact_city: str = "",
        contact_state: str = "",
        contact_country: str = "",
        contact_postalcode: str = "",
        # Communication protocols (optional)
        communication_protocols: Optional[List[str]] = None
    ) -> str:
        """
        Build X12 trading partner component XML.

        Args:
            name: Trading partner component name
            folder_name: Folder to create the component in
            description: Component description
            classification: Partner classification (mytradingpartner, mycompany)

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
            - contact_*: Contact information fields

            Communication parameters:
            - communication_protocols: List of protocol names (e.g., ['ftp', 'http'])

        Returns:
            Complete X12 trading partner component XML
        """
        # Validate required parameters
        self.validate(name=name, isa_interchangeid=isa_interchangeid)

        # Build ContactInfo XML with attributes
        contact_info_xml = self._build_contact_info_attrs(
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            contact_fax=contact_fax,
            contact_address=contact_address,
            contact_address2=contact_address2,
            contact_city=contact_city,
            contact_state=contact_state,
            contact_country=contact_country,
            contact_postalcode=contact_postalcode
        )

        # Build Communication XML
        communication_xml = build_communication_xml(communication_protocols)

        # Build TradingPartner inner XML
        trading_partner_xml = f'''<TradingPartner classification="{classification}" standard="x12">
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
              {communication_xml}
            </PartnerCommunication>
          </TradingPartner>'''

        # Wrap in Component XML envelope
        return ComponentXMLWrapper.wrap(
            name=name,
            component_type="tradingpartner",
            folder_name=folder_name,
            inner_xml=trading_partner_xml,
            description=description
        )

    def validate(self, **params) -> None:
        """
        Validate X12-specific parameters.

        Args:
            **params: Parameters to validate

        Raises:
            ValueError: If validation fails
        """
        name = params.get("name")
        if not name:
            raise ValueError("Trading partner name is required")

        # ISA interchange ID is important for X12
        isa_interchangeid = params.get("isa_interchangeid", "")
        if not isa_interchangeid:
            # Warning: not strictly required but recommended
            pass

    def _build_contact_info_attrs(
        self,
        contact_name: str = "",
        contact_email: str = "",
        contact_phone: str = "",
        contact_fax: str = "",
        contact_address: str = "",
        contact_address2: str = "",
        contact_city: str = "",
        contact_state: str = "",
        contact_country: str = "",
        contact_postalcode: str = ""
    ) -> str:
        """
        Build ContactInfo XML with attributes (X12 style).

        X12 uses attribute-based contact info instead of nested elements.

        Args:
            contact_*: Contact information fields

        Returns:
            ContactInfo XML string
        """
        contact_attrs = []

        if contact_name:
            contact_attrs.append(f'name="{self._escape_xml(contact_name)}"')
        if contact_email:
            contact_attrs.append(f'email="{self._escape_xml(contact_email)}"')
        if contact_phone:
            contact_attrs.append(f'phone="{self._escape_xml(contact_phone)}"')
        if contact_fax:
            contact_attrs.append(f'fax="{self._escape_xml(contact_fax)}"')
        if contact_address:
            contact_attrs.append(f'address1="{self._escape_xml(contact_address)}"')
        if contact_address2:
            contact_attrs.append(f'address2="{self._escape_xml(contact_address2)}"')
        if contact_city:
            contact_attrs.append(f'city="{self._escape_xml(contact_city)}"')
        if contact_state:
            contact_attrs.append(f'state="{self._escape_xml(contact_state)}"')
        if contact_country:
            contact_attrs.append(f'country="{self._escape_xml(contact_country)}"')
        if contact_postalcode:
            contact_attrs.append(f'postalcode="{self._escape_xml(contact_postalcode)}"')

        if contact_attrs:
            return f'<ContactInfo {" ".join(contact_attrs)} />'
        else:
            return "<ContactInfo />"
