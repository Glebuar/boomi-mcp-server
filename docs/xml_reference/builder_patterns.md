# XML Builder Patterns and Best Practices

**Date**: 2025-01-17
**Status**: Architecture Guide

---

## Overview

This document describes the builder pattern architecture used for Boomi component XML generation.

---

## Architecture Principles

### 1. Separation of Concerns

```
┌─────────────────────────────────────────┐
│ MCP Tool (trading_partners.py)          │  ← High-level API
│ - Handles user input                     │
│ - Calls appropriate builder              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Standard Builder (x12_builder.py)       │  ← Business logic
│ - Validates parameters                   │
│ - Builds standard-specific XML           │
│ - Uses communication builders            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Communication Builders (communication.py)│  ← Reusable components
│ - Protocol-specific templates            │
│ - Shared across ALL component types     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Component Wrapper (base_builder.py)     │  ← Infrastructure
│ - Generic <bns:Component> envelope       │
│ - XML escaping utilities                 │
└─────────────────────────────────────────┘
```

### 2. Builder Pattern

**Classic Gang of Four pattern** for constructing complex objects:

```python
# Abstract base
class TradingPartnerBuilder(ABC):
    @abstractmethod
    def build(**params) -> str:
        """Build complete component XML"""

    def validate(**params) -> None:
        """Validate before building"""

# Concrete implementation
class X12TradingPartnerBuilder(TradingPartnerBuilder):
    def build(self, name, isa_id, ...) -> str:
        # 1. Validate
        self.validate(name=name, isa_id=isa_id)

        # 2. Build parts
        contact_xml = self._build_contact_info(...)
        comm_xml = build_communication_xml([...])

        # 3. Assemble
        trading_partner_xml = f'''<TradingPartner>
            {contact_xml}
            {partner_info_xml}
            {comm_xml}
        </TradingPartner>'''

        # 4. Wrap
        return ComponentXMLWrapper.wrap(...)
```

### 3. Registry Pattern

Easy lookup of builders without tight coupling:

```python
# builders/__init__.py
STANDARD_BUILDERS = {
    "x12": X12TradingPartnerBuilder,
    "edifact": EDIFACTTradingPartnerBuilder,
    # ...
}

def get_builder_for_standard(standard: str) -> type:
    builder_class = STANDARD_BUILDERS.get(standard.lower())
    if not builder_class:
        raise ValueError(f"Unsupported standard: {standard}")
    return builder_class

# Usage in tool
builder_class = get_builder_for_standard("x12")
builder = builder_class()
xml = builder.build(...)
```

### 4. Composition Over Inheritance

Communication builders are **composed**, not inherited:

```python
# GOOD: Composition
class X12TradingPartnerBuilder(TradingPartnerBuilder):
    def build(self, ..., communication_protocols):
        # Use communication builders via function call
        comm_xml = build_communication_xml(communication_protocols)

# BAD: Inheritance
class X12WithFTPBuilder(X12Builder, FTPBuilder):  # ❌ Don't do this
    pass
```

---

## Design Patterns Used

### Pattern 1: Template Method

Base class defines algorithm, subclasses fill in details:

```python
class TradingPartnerBuilder(BaseXMLBuilder):
    def build(self, **params) -> str:
        # Template method - subclasses override
        self.validate(**params)           # Hook 1
        inner_xml = self._build_inner()   # Hook 2
        return ComponentXMLWrapper.wrap(inner_xml)

    @abstractmethod
    def _build_inner(self) -> str:
        """Subclass implements this"""
```

### Pattern 2: Strategy

Different builders (strategies) for different standards:

```python
# Client code doesn't know which builder
standard = user_input.get("standard")
builder = get_builder_for_standard(standard)  # Strategy selection
xml = builder.build(**params)                 # Use strategy
```

### Pattern 3: Factory

Builder registry acts as factory:

```python
def get_builder_for_standard(standard: str) -> TradingPartnerBuilder:
    """Factory method - creates appropriate builder"""
    return STANDARD_BUILDERS[standard]()
```

---

## Best Practices

### ✅ DO: Validate Early

```python
def build(self, name, isa_id, **params):
    # Validate BEFORE building anything
    if not name:
        raise ValueError("Component name is required")
    if not isa_id:
        raise ValueError("ISA Interchange ID is required for X12")

    # Now build with confidence
    return self._build_xml(name, isa_id, **params)
```

### ✅ DO: Escape XML Content

```python
def _escape_xml(self, text: str) -> str:
    """Always escape user input"""
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;'
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text

# Usage
name = self._escape_xml(user_name)  # Safe!
```

### ✅ DO: Use Clear Names

```python
# GOOD: Descriptive method names
def build_x12_control_info(self, isa_id, gs_code):
    ...

def build_communication_options(self, protocols):
    ...

# BAD: Vague names
def build_stuff(self, data):
    ...

def process(self, x, y):
    ...
```

### ✅ DO: Single Responsibility

```python
# GOOD: One responsibility per class
class AS2ProtocolBuilder:
    """Builds ONLY AS2 communication XML"""

class X12TradingPartnerBuilder:
    """Builds ONLY X12 trading partner XML"""

# BAD: Too many responsibilities
class UniversalBuilder:
    def build_x12(self, ...):
        ...
    def build_edifact(self, ...):
        ...
    def build_process(self, ...):
        ...
    # ... 50 more methods
```

### ❌ DON'T: Hardcode Values

```python
# BAD: Hardcoded
xml = f'<Component type="tradingpartner" folderName="Home">'

# GOOD: Parameterized
xml = f'<Component type="{component_type}" folderName="{folder_name}">'
```

### ❌ DON'T: Return None on Error

```python
# BAD: Silent failure
def build(self, name):
    if not name:
        return None  # Caller must check!
    return self._build(name)

# GOOD: Fail loudly
def build(self, name):
    if not name:
        raise ValueError("Name is required")
    return self._build(name)
```

### ❌ DON'T: Mix Concerns

```python
# BAD: Builder talks to database
class X12Builder:
    def build(self, name):
        user = database.get_user()  # ❌ Wrong layer!
        return f'<Component name="{name}" owner="{user}">'

# GOOD: Builder only builds
class X12Builder:
    def build(self, name, owner):  # ✅ Data passed in
        return f'<Component name="{name}" owner="{owner}">'
```

---

## Testing Strategy

### Unit Test Each Builder

```python
def test_x12_builder_minimal():
    """Test X12 builder with minimal parameters"""
    builder = X12TradingPartnerBuilder()

    xml = builder.build(
        name="Test Partner",
        isa_interchangeid="123456789"
    )

    assert '<TradingPartner classification="mytradingpartner" standard="x12">' in xml
    assert 'interchangeid="123456789"' in xml
    assert 'type="tradingpartner"' in xml

def test_x12_builder_validates():
    """Test X12 builder validation"""
    builder = X12TradingPartnerBuilder()

    with pytest.raises(ValueError, match="name is required"):
        builder.build(name="")
```

### Integration Test with Boomi API

```python
def test_x12_create_via_api(boomi_client):
    """Test X12 partner creation end-to-end"""
    builder = X12TradingPartnerBuilder()

    xml = builder.build(
        name=f"Test-{uuid.uuid4()}",
        folder_name="Test/Partners",
        isa_interchangeid="999999999"
    )

    # Create via API
    result = boomi_client.component.create(xml)

    assert result.id_ is not None
    assert result.name.startswith("Test-")

    # Cleanup
    boomi_client.component.delete(result.id_)
```

---

## Extension Points

### Adding a New EDI Standard

1. **Create builder class**:
   ```python
   # builders/custom_builder.py
   class CustomTradingPartnerBuilder(TradingPartnerBuilder):
       def get_standard_name(self) -> str:
           return "custom"

       def build(self, **params) -> str:
           # Implement custom standard logic
           ...
   ```

2. **Register in registry**:
   ```python
   # builders/__init__.py
   from .custom_builder import CustomTradingPartnerBuilder

   STANDARD_BUILDERS = {
       "x12": X12TradingPartnerBuilder,
       "custom": CustomTradingPartnerBuilder,  # ← Add here
   }
   ```

3. **Done!** Tool will automatically use new builder

### Adding a New Communication Protocol

1. **Create protocol builder**:
   ```python
   # builders/communication.py
   class MyProtocolBuilder(CommunicationProtocolBuilder):
       def get_protocol_name(self) -> str:
           return "myprotocol"

       def build(self, **params) -> str:
           return '''<CommunicationOption method="myprotocol">
               <!-- protocol-specific XML -->
           </CommunicationOption>'''
   ```

2. **Register in registry**:
   ```python
   PROTOCOL_BUILDERS = {
       "as2": AS2ProtocolBuilder,
       "myprotocol": MyProtocolBuilder,  # ← Add here
   }
   ```

3. **Done!** Available in all components that use communication

---

## Performance Considerations

### String Concatenation

```python
# SLOW: Multiple string concatenations
xml = ""
xml += "<Component>"
xml += f"<name>{name}</name>"
xml += f"<type>{type}</type>"
xml += "</Component>"

# FAST: Single f-string
xml = f'''<Component>
    <name>{name}</name>
    <type>{type}</type>
</Component>'''

# FASTEST (for very large XML): String builder
from io import StringIO
builder = StringIO()
builder.write("<Component>")
builder.write(f"<name>{name}</name>")
# ...
xml = builder.getvalue()
```

### Caching

```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def get_builder_for_standard(standard: str) -> type:
    """Cached builder lookup"""
    return STANDARD_BUILDERS[standard]
```

---

## Migration from Old Code

### Before (Function-based)

```python
# trading_partners.py (old)
def build_trading_partner_xml_x12(name, folder, ...):
    """Monolithic function - 200 lines"""
    # ... 200 lines of XML building ...
    return xml
```

### After (Class-based)

```python
# builders/x12_builder.py (new)
class X12TradingPartnerBuilder(TradingPartnerBuilder):
    """Focused, testable, reusable"""

    def build(self, name, folder, ...):
        """~50 lines - uses composition"""
        contact_xml = self._build_contact_info(...)
        comm_xml = build_communication_xml(...)
        return ComponentXMLWrapper.wrap(...)

    def _build_contact_info(self, ...):
        """Separate concern"""
        ...
```

**Benefits**:
- ✅ Easier to test (can test each method)
- ✅ Easier to reuse (import and instantiate)
- ✅ Easier to extend (subclass or compose)
- ✅ Easier to maintain (smaller, focused modules)

---

## References

- **Design Patterns**: "Gang of Four" (Gamma et al.)
- **Clean Code**: Robert C. Martin
- **Effective Python**: Brett Slatkin
- **Boomi API Docs**: https://help.boomi.com/docs/atomsphere/integration/api/
