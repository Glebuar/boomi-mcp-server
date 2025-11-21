"""
YAML Parser for Boomi process configurations.

Converts YAML strings to validated Pydantic models for the orchestrator.
Supports both single-process and multi-component formats.
"""

import yaml
from typing import List, Dict, Any
from ..models.process_models import ComponentSpec, ProcessConfig, ShapeConfig


def parse_yaml_to_specs(yaml_content: str) -> List[ComponentSpec]:
    """
    Parse YAML process configuration to ComponentSpec list.

    Supports two formats:

    1. Single Process (shorthand):
        name: "My Process"
        folder_name: "Integrations"
        description: "Process description"
        shapes:
          - type: start
            name: start
          - type: message
            name: msg
            config:
              message_text: "Hello"
          - type: stop
            name: end

    2. Multi-Component (with dependencies):
        components:
          - name: "Transform Map"
            type: map
            dependencies: []
            config:
              source_profile: "SF_Customer"

          - name: "Main Process"
            type: process
            dependencies: ["Transform Map"]
            config:
              name: "Main Process"
              shapes:
                - type: start
                  name: start
                - type: map
                  name: transform
                  config:
                    map_ref: "Transform Map"
                - type: stop
                  name: end

    Args:
        yaml_content: YAML string to parse

    Returns:
        List of ComponentSpec objects ready for orchestrator

    Raises:
        yaml.YAMLError: If YAML syntax is invalid
        ValidationError: If data doesn't match Pydantic schemas

    Examples:
        # Single process
        yaml_str = '''
        name: "Hello World"
        shapes:
          - type: start
            name: start
          - type: message
            name: msg
            config:
              message_text: "Hello from Boomi!"
          - type: stop
            name: end
        '''
        specs = parse_yaml_to_specs(yaml_str)
        # Returns: [ComponentSpec(name="Hello World", type="process", ...)]

        # Multi-component
        yaml_str = '''
        components:
          - name: "Map A"
            type: map
            dependencies: []
          - name: "Process B"
            type: process
            dependencies: ["Map A"]
            config:
              name: "Process B"
              shapes: [...]
        '''
        specs = parse_yaml_to_specs(yaml_str)
        # Returns: [ComponentSpec(name="Map A", ...), ComponentSpec(name="Process B", ...)]
    """
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {str(e)}") from e

    if not isinstance(data, dict):
        raise ValueError("YAML must contain a dictionary at root level")

    # Check if multi-component format
    if 'components' in data:
        return _parse_multi_component(data['components'])
    else:
        return _parse_single_process(data)


def _parse_single_process(data: Dict[str, Any]) -> List[ComponentSpec]:
    """
    Parse single process shorthand format.

    Args:
        data: Dict with process fields (name, shapes, etc.)

    Returns:
        Single-element list with ComponentSpec for the process

    Raises:
        ValidationError: If data doesn't match ProcessConfig schema
    """
    # Validate as ProcessConfig
    process_config = ProcessConfig(**data)

    # Wrap in ComponentSpec
    spec = ComponentSpec(
        name=process_config.name,
        type='process',
        dependencies=[],  # Single process has no explicit dependencies
        config=process_config.model_dump()  # Convert to dict for orchestrator
    )

    return [spec]


def _parse_multi_component(components_data: List[Dict[str, Any]]) -> List[ComponentSpec]:
    """
    Parse multi-component format with dependencies.

    Args:
        components_data: List of component dicts

    Returns:
        List of ComponentSpec objects

    Raises:
        ValidationError: If any component doesn't match schemas
    """
    specs = []

    for comp_data in components_data:
        # Parse component spec
        comp_type = comp_data.get('type', 'process')

        # For process components, validate config as ProcessConfig
        if comp_type == 'process' and 'config' in comp_data:
            config_data = comp_data['config']
            if isinstance(config_data, dict):
                # Validate as ProcessConfig
                process_config = ProcessConfig(**config_data)
                comp_data['config'] = process_config.model_dump()

        # Create ComponentSpec
        spec = ComponentSpec(**comp_data)
        specs.append(spec)

    return specs


def validate_yaml_syntax(yaml_content: str) -> tuple[bool, str]:
    """
    Validate YAML syntax without full parsing.

    Args:
        yaml_content: YAML string to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        valid, error = validate_yaml_syntax(yaml_str)
        if not valid:
            print(f"YAML error: {error}")
    """
    try:
        yaml.safe_load(yaml_content)
        return True, ""
    except yaml.YAMLError as e:
        return False, str(e)


def yaml_to_dict(yaml_content: str) -> Dict[str, Any]:
    """
    Convert YAML to dictionary without validation.

    Useful for debugging or custom processing.

    Args:
        yaml_content: YAML string

    Returns:
        Parsed dictionary

    Raises:
        yaml.YAMLError: If YAML syntax is invalid
    """
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {str(e)}") from e


# Example YAML templates for documentation
SINGLE_PROCESS_EXAMPLE = """
# Single Process Example
name: "SF to NS ETL"
folder_name: "Integrations/Production"
description: "Sync customers from Salesforce to NetSuite"

shapes:
  - type: start
    name: start
    userlabel: "Start"

  - type: connector
    name: sf_query
    userlabel: "Query Salesforce"
    config:
      connector_id: "abc-123-def"
      operation: "query"
      object_type: "Account"

  - type: map
    name: transform
    userlabel: "Transform Data"
    config:
      map_id: "xyz-789-uvw"

  - type: connector
    name: ns_upsert
    userlabel: "Upsert to NetSuite"
    config:
      connector_id: "mno-456-pqr"
      operation: "upsert"

  - type: stop
    name: end
    userlabel: "Stop"
"""

MULTI_COMPONENT_EXAMPLE = """
# Multi-Component Example with Dependencies
components:
  # Component 1: Map (no dependencies)
  - name: "Customer Transform"
    type: map
    dependencies: []
    config:
      source_profile: "Salesforce_Customer"
      target_profile: "NetSuite_Customer"

  # Component 2: Connection (no dependencies)
  - name: "OpenAI API"
    type: connection
    dependencies: []
    config:
      connector_type: "http"
      url: "https://api.openai.com/v1/chat/completions"

  # Component 3: Main Process (depends on both above)
  - name: "SF to NS with AI"
    type: process
    dependencies: ["Customer Transform", "OpenAI API"]
    config:
      name: "SF to NS with AI"
      folder_name: "Integrations/Production"
      description: "ETL with AI enrichment"
      shapes:
        - type: start
          name: start

        - type: connector
          name: sf_query
          config:
            connector_id: "sf-connector-id"
            operation: "query"

        - type: map
          name: transform
          config:
            map_ref: "Customer Transform"  # Reference by name!

        - type: connector
          name: ai_enrich
          config:
            connection_ref: "OpenAI API"  # Reference by name!

        - type: connector
          name: ns_upsert
          config:
            connector_id: "ns-connector-id"
            operation: "upsert"

        - type: stop
          name: end
"""
