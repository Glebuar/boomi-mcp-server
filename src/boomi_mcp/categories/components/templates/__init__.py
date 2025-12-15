"""
XML Templates for Boomi Components.

This package contains XML templates for various Boomi component types.
Templates are organized by:
- communication/: Communication protocol templates (AS2, FTP, HTTP, etc.)
- standards/: EDI standard templates (X12, EDIFACT, HL7, etc.)

Note: Currently, templates are embedded in builder classes.
This structure is reserved for future externalization of templates
into separate .xml files if needed for better maintainability.

Future Usage:
    # When templates are externalized:
    from boomi_mcp.categories.components.templates import load_template

    template_xml = load_template('standards/x12_template.xml')
"""

# Placeholder for future template loading functionality
def load_template(template_name: str) -> str:
    """
    Load XML template from file.

    Args:
        template_name: Template file name (e.g., 'standards/x12_template.xml')

    Returns:
        Template XML string

    Raises:
        FileNotFoundError: If template file doesn't exist

    Note:
        Currently not implemented. Templates are embedded in builder classes.
    """
    raise NotImplementedError(
        "Template externalization not yet implemented. "
        "Templates are currently embedded in builder classes."
    )
