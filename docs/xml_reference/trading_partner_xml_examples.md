# Trading Partner XML Examples

**Status**: Historical Reference (Extracted from working implementation)
**Date**: 2025-01-17
**Source**: `src/boomi_mcp/categories/components/trading_partners.py` (lines 575-1420)

---

## Purpose

These are **WORKING, TESTED** XML examples from production Trading Partner implementation.
While Trading Partners now use JSON API, these patterns are **ESSENTIAL** for:

- Process components (XML only)
- Connection components (XML only)
- Any component using Communication protocols

---

## Complete X12 Trading Partner Example

### Minimal X12 Trading Partner

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bns:Component xmlns:bns="http://api.platform.boomi.com/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               type="tradingpartner"
               name="ACME Corporation"
               folderName="Trading Partners/Vendors">
    <bns:encryptedValues />
    <bns:description>X12 EDI Trading Partner</bns:description>
    <bns:object>
        <TradingPartner classification="mytradingpartner" standard="x12">
            <ContactInfo />
            <PartnerInfo>
                <X12PartnerInfo>
                    <X12Options
                        acknowledgementoption="donotackitem"
                        envelopeoption="groupall"
                        fileDelimiter="stardelimited"
                        filteracknowledgements="false"
                        outboundInterchangeValidation="false"
                        outboundValidationOption="filterError"
                        rejectDuplicateInterchange="false"
                        segmentchar="newline" />
                    <X12ControlInfo>
                        <ISAControlInfo
                            ackrequested="false"
                            authorinfoqual="00"
                            interchangeid="123456789"
                            interchangeidqual="01"
                            securityinfoqual="00"
                            testindicator="P" />
                        <GSControlInfo respagencycode="T" />
                    </X12ControlInfo>
                </X12PartnerInfo>
            </PartnerInfo>
            <PartnerCommunication>
              <CommunicationOptions />
            </PartnerCommunication>
          </TradingPartner>
    </bns:object>
</bns:Component>
```

### X12 with Contact Info

```xml
<TradingPartner classification="mytradingpartner" standard="x12">
    <ContactInfo
        name="John Smith"
        email="john.smith@acme.com"
        phone="+1-555-0100"
        fax="+1-555-0101"
        address1="123 Main Street"
        address2="Suite 100"
        city="New York"
        state="NY"
        country="USA"
        postalcode="10001" />
    <PartnerInfo>
        <!-- Same as above -->
    </PartnerInfo>
    <PartnerCommunication>
        <CommunicationOptions />
    </PartnerCommunication>
</TradingPartner>
```

### X12 with FTP Communication

```xml
<PartnerCommunication>
  <CommunicationOptions>
    <CommunicationOption commOption="default" method="ftp">
      <CommunicationSettings docType="default">
        <SettingsObject useMyTradingPartnerSettings="false">
          <FTPSettings connectionMode="PASV" host="ftp.acme.com" port="21">
            <AuthSettings user="ediuser"/>
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
    </CommunicationOption>
  </CommunicationOptions>
</PartnerCommunication>
```

---

## Communication Protocol Patterns

### AS2 Protocol

```xml
<CommunicationOption commOption="default" method="as2">
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
          <MessageOptions
            compressed="false"
            dataContentType="application/xml"
            encrypted="false"
            encryptionAlgorithm="tripledes"
            signed="false"
            signingDigestAlg="SHA1"/>
          <MDNOptions
            failOnNegativeMDN="true"
            mdnDigestAlg="SHA1"
            requestMDN="false"
            signed="false"
            synchronous="true"/>
        </AS2SendAction>
        <DataProcessing sequence="pre">
          <dataprocess/>
        </DataProcessing>
      </ActionObject>
    </ActionObjects>
  </CommunicationSettings>
</CommunicationOption>
```

### HTTP Protocol

```xml
<CommunicationOption commOption="default" method="http">
  <CommunicationSettings docType="default">
    <SettingsObject useMyTradingPartnerSettings="false">
      <HttpSettings
        authenticationType="NONE"
        connectTimeout="15000"
        readTimeout="60000"
        url="">
        <AuthSettings user=""/>
        <SSLOptions clientauth="false" trustServerCert="false"/>
      </HttpSettings>
    </ SettingsObject>
    <ActionObjects>
      <ActionObject type="Get" useMyTradingPartnerOptions="false">
        <HttpGetAction
          dataContentType="application/xml"
          followRedirects="false"
          methodType="GET"
          returnErrors="false"/>
        <DataProcessing sequence="post">
          <dataprocess/>
        </DataProcessing>
      </ActionObject>
      <ActionObject type="Send" useMyTradingPartnerOptions="false">
        <HttpSendAction
          dataContentType="application/xml"
          followRedirects="false"
          methodType="POST"
          returnErrors="false"/>
        <DataProcessing sequence="pre">
          <dataprocess/>
        </DataProcessing>
      </ActionObject>
    </ActionObjects>
  </CommunicationSettings>
</CommunicationOption>
```

### SFTP Protocol

```xml
<CommunicationOption commOption="default" method="sftp">
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
</CommunicationOption>
```

### Disk Protocol

```xml
<CommunicationOption commOption="default" method="disk">
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
</CommunicationOption>
```

---

## Key XML Patterns

### Component Wrapper Pattern

**Every component** follows this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bns:Component
    xmlns:bns="http://api.platform.boomi.com/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    type="{component_type}"      <!-- tradingpartner, process, connection -->
    name="{component_name}"
    folderName="{folder_path}">

    <bns:encryptedValues />      <!-- Optional encrypted values -->
    <bns:description>{description}</bns:description>

    <bns:object>
        <!-- Component-specific XML goes here -->
        <TradingPartner>...</TradingPartner>
        <!-- OR -->
        <Process>...</Process>
        <!-- OR -->
        <Connection>...</Connection>
    </bns:object>
</bns:Component>
```

**This wrapper is REUSABLE** - see `ComponentXMLWrapper` class.

### Communication Options Pattern

Communication protocols are **shared across all component types**:
- Trading Partners
- Processes (for listeners, web services)
- Connections

Structure is always:
```xml
<PartnerCommunication>  <!-- Or ProcessCommunication for processes -->
  <CommunicationOptions>
    <CommunicationOption commOption="default" method="{protocol}">
      <CommunicationSettings docType="default">
        <SettingsObject>
          <!-- Protocol-specific settings -->
        </SettingsObject>
        <ActionObjects>
          <!-- Get/Send/Listen actions -->
        </ActionObjects>
      </CommunicationSettings>
    </CommunicationOption>
  </CommunicationOptions>
</PartnerCommunication>
```

---

## XML Special Characters

**Always escape these characters** in attribute values and text content:

| Character | Escaped Form | Example |
|-----------|--------------|---------|
| `&` | `&amp;` | `Smith & Co` → `Smith &amp; Co` |
| `<` | `&lt;` | `value < 10` → `value &lt; 10` |
| `>` | `&gt;` | `value > 5` → `value &gt; 5` |
| `"` | `&quot;` | In attributes: `name="John &quot;Johnny&quot; Smith"` |
| `'` | `&apos;` | In attributes: `name='John &apos;Johnny&apos; Smith'` |

See `BaseXMLBuilder._escape_xml()` method.

---

## Testing Notes

### What Was Tested

✅ X12 with all communication protocols (FTP, SFTP, HTTP, AS2, Disk, MLLP, OFTP)
✅ Contact info with special characters
✅ All ISA/GS control info combinations
✅ Empty CommunicationOptions

### What Works

- Component creation via Component API (`boomi_client.component.create(xml)`)
- All 7 communication protocols
- Nested folder paths (`"Parent/Child/Grandchild"`)
- Special characters in names/descriptions (when properly escaped)

### What to Watch Out For

⚠️ **Invalid XML** - Single unescaped `&` breaks entire request
⚠️ **Missing namespaces** - `xmlns:bns` is required
⚠️ **Wrong type attribute** - Must match component type exactly
⚠️ **Empty required fields** - Some fields can't be empty strings (use appropriate defaults)

---

## Future Usage

When implementing **Process components**, reuse:
1. `ComponentXMLWrapper` - Same wrapper, different `type` attribute
2. `build_communication_xml()` - Identical communication protocol support
3. Validation patterns - Same XML escaping and structure validation

When implementing **Connection components**, reuse:
1. All of the above
2. Connection-specific builders (to be created following same pattern)

---

## Source Code References

- **Original implementation**: `src/boomi_mcp/categories/components/trading_partners.py` (archived)
- **New builders**: `src/boomi_mcp/categories/components/builders/`
- **X12 builder**: `src/boomi_mcp/categories/components/builders/x12_builder.py`
- **Communication builders**: `src/boomi_mcp/categories/components/builders/communication.py`
