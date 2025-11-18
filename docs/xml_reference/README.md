# XML Reference Documentation

**Purpose**: Preserve XML building patterns and examples for future component implementations.

**Date Created**: 2025-01-17
**Status**: Historical Reference

---

## Why This Documentation Exists

### Background

Trading Partners in Boomi have **TWO** APIs:
1. **TradingPartnerComponent API** (JSON-based) ✅ Preferred
2. **Component API** (XML-based) ⚠️ More complex

We initially implemented using the Component API (XML), which required building
complex XML structures. While we're **migrating to JSON API** for Trading Partners,
the XML building patterns are **ESSENTIAL for other component types**:

- **Process Components** (XML only)
- **Connection Components** (XML only)
- **Web Service Components** (XML only)
- **Map Components** (XML only)

### What's Preserved

1. **Working XML Examples** - Tested in production
2. **Builder Patterns** - Reusable across component types
3. **Communication Protocol Templates** - Shared across all components
4. **Lessons Learned** - What works, what doesn't

---

## New Architecture (Post-Refactoring)

### Directory Structure

```
src/boomi_mcp/categories/components/
├── builders/                          # XML builder classes (REUSABLE!)
│   ├── __init__.py                   # Builder registry
│   ├── base_builder.py               # Abstract base classes
│   ├── communication.py              # Protocol builders (AS2, FTP, HTTP, etc.)
│   ├── x12_builder.py                # X12 standard builder
│   └── ... (other standards)
│
├── templates/                         # Future: External templates
│   ├── __init__.py
│   ├── communication/
│   └── standards/
│
└── trading_partners.py                # Main tool (will use JSON API)
```

### Key Classes

**`ComponentXMLWrapper`**
- Generic wrapper for ALL component types
- Adds `<bns:Component>` envelope with metadata
- **Reusable**: Process, Connection, Trading Partner, etc.

**`CommunicationProtocolBuilder`**
- Base class for AS2, FTP, HTTP, SFTP, etc.
- **Shared**: Communication protocols work the same across all components
- **Extensible**: Easy to add new protocols

**`TradingPartnerBuilder`**
- Abstract base for EDI standard builders (X12, EDIFACT, HL7)
- **Pattern**: Each standard extends this class
- **Example**: `X12TradingPartnerBuilder`

---

## How to Use Builders (Future Components)

### Example: Creating Process Component (Future Implementation)

```python
from boomi_mcp.categories.components.builders import ComponentXMLWrapper
from boomi_mcp.categories.components.builders.communication import build_communication_xml

# Build process-specific XML
process_xml = """<Process>
    <ProcessSteps>
        <StartShape/>
        <EndShape/>
    </ProcessSteps>
</Process>"""

# Add communication if needed
comm_xml = build_communication_xml(['http', 'as2'])

# Wrap in Component envelope
component_xml = ComponentXMLWrapper.wrap(
    name="MyProcess",
    component_type="process",
    folder_name="Integrations/Production",
    inner_xml=process_xml,
    description="My integration process"
)

# Create via Component API
result = boomi_client.component.create(component_xml)
```

### Example: Using X12 Builder (Current Trading Partners)

```python
from boomi_mcp.categories.components.builders import X12TradingPartnerBuilder

builder = X12TradingPartnerBuilder()

xml = builder.build(
    name="ACME Corporation",
    folder_name="Trading Partners/Vendors",
    isa_interchangeid="123456789",
    isa_interchangeidqual="01",
    communication_protocols=['ftp', 'http']
)

result = boomi_client.component.create(xml)
```

---

## Reference Documents

- [Trading Partner XML Examples](./trading_partner_xml_examples.md) - Working X12, EDIFACT, HL7 examples
- [Builder Patterns](./builder_patterns.md) - Design patterns and best practices
- [Communication Protocols](./communication_protocols.md) - Protocol template reference

---

## Migration Path

**Phase 1**: ✅ Extract builders to reusable modules
**Phase 2**: 🔄 Refactor Trading Partners to JSON API
**Phase 3**: ⏳ Implement Process components using extracted builders
**Phase 4**: ⏳ Implement Connection components using extracted builders

---

## Lessons Learned

### What Works Well

1. **Separation of Concerns**: Communication builders separate from standard builders
2. **Builder Pattern**: Easy to understand, test, and extend
3. **ComponentXMLWrapper**: Reusable across ALL component types
4. **Registry Pattern**: Easy lookup by standard/protocol name

### What to Avoid

1. **❌ Inline XML Strings**: Hard to read, maintain, test
2. **❌ Monolithic Functions**: 2,683-line files are unmaintainable
3. **❌ No Validation**: Validate parameters before building XML
4. **❌ No Escaping**: Always escape XML special characters

### Best Practices

1. ✅ **Class-based builders** over functions
2. ✅ **Separate templates** from logic (future externalization)
3. ✅ **Validate early** - fail fast with clear errors
4. ✅ **Reuse components** - communication protocols, wrappers, etc.
5. ✅ **Test builders** - unit test each builder independently

---

## Contact

For questions about this architecture, see:
- `src/boomi_mcp/categories/components/builders/` - Implementation
- `MCP_TOOL_DESIGN.md` - Overall tool design
- This documentation - Historical context
