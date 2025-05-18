from pathlib import Path
from fastmcp import FastMCP
from .auth import get_client

mcp = FastMCP(
    name="Boomi MCP",
    instructions=(
        "Call these tools to interact with the Boomi Platform API. "
        "NEVER ask the user for credentials."
    ),
)


@mcp.tool()
def create_component(xml_path: str) -> dict:
    """Create a Boomi component from an XML file."""
    boomi = get_client()
    comp = boomi.components.create(Path(xml_path))
    return comp.model_dump()


@mcp.tool()
def get_component(component_id: str) -> dict:
    """Fetch a component by its Boomi ID."""
    return get_client().components.get(component_id).model_dump()


@mcp.tool()
def deploy_package(environment_id: str, package_id: str) -> dict:
    """Deploy an existing package to a target environment."""
    return get_client().deployments.deploy(environment_id, package_id)
