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
def update_component(component_id: str, xml: str) -> None:
    """Update a component's XML."""
    get_client().components.update(component_id, xml)


@mcp.tool()
def delete_component(component_id: str) -> None:
    """Delete a component by ID."""
    get_client().components.delete(component_id)


@mcp.tool()
def get_component(component_id: str) -> dict:
    """Fetch a component by its Boomi ID."""
    return get_client().components.get(component_id).model_dump()


@mcp.tool()
def create_package(component_id: str, package_version: str | None = None,
                    notes: str | None = None) -> dict:
    """Create a package from a component."""
    return get_client().packages.create(component_id, package_version, notes)


@mcp.tool()
def deploy_package(environment_id: str, package_id: str) -> dict:
    """Deploy an existing package to a target environment."""
    return get_client().deployments.deploy(environment_id, package_id)


@mcp.tool()
def create_folder(name: str, parent_id: str | None = None) -> dict:
    """Create a folder."""
    return get_client().folders.create(name, parent_id)


@mcp.tool()
def get_folder(folder_id: str) -> dict:
    """Fetch a folder by ID."""
    return get_client().folders.get(folder_id)


@mcp.tool()
def delete_folder(folder_id: str) -> None:
    """Delete a folder."""
    get_client().folders.delete(folder_id)


@mcp.tool()
def list_atoms() -> list:
    """List available atoms."""
    return get_client().atoms.list()


@mcp.tool()
def list_environments() -> list:
    """List environments."""
    return get_client().environments.list()


@mcp.tool()
def query_runs(query: dict) -> dict:
    """Query execution records."""
    return get_client().runs.list(query)


@mcp.tool()
def get_run_log(execution_id: str) -> str:
    """Get a URL to the execution log."""
    return get_client().runs.log(execution_id)


@mcp.tool()
def get_schedule(schedule_id: str) -> dict:
    """Fetch schedule info."""
    return get_client().schedules.get(schedule_id)


@mcp.tool()
def update_schedule(schedule_id: str, body: dict) -> dict:
    """Update a schedule."""
    return get_client().schedules.update(schedule_id, body)


@mcp.tool()
def query_schedules(query: dict) -> dict:
    """Query schedules."""
    return get_client().schedules.query(query)


@mcp.tool()
def bulk_schedules(ids: list[str]) -> dict:
    """Get schedules in bulk."""
    return get_client().schedules.bulk(ids)


@mcp.tool()
def get_extensions(environment_id: str) -> dict:
    """Get environment extensions."""
    return get_client().extensions.get(environment_id)


@mcp.tool()
def update_extensions(environment_id: str, body: dict) -> dict:
    """Update environment extensions."""
    return get_client().extensions.update(environment_id, body)


@mcp.tool()
def query_extensions(query: dict) -> dict:
    """Query extensions."""
    return get_client().extensions.query(query)


@mcp.tool()
def query_extension_field_summary(query: dict) -> dict:
    """Query connection field extension summary."""
    return get_client().extensions.query_conn_field_summary(query)


@mcp.tool()
def create_runtime_release(body: dict) -> dict:
    """Create a runtime release schedule."""
    return get_client().runtime.create(body)


@mcp.tool()
def get_runtime_release(cid: str) -> dict:
    """Get runtime release details."""
    return get_client().runtime.get(cid)


@mcp.tool()
def update_runtime_release(cid: str, body: dict) -> dict:
    """Update runtime release."""
    return get_client().runtime.update(cid, body)


@mcp.tool()
def delete_runtime_release(cid: str) -> None:
    """Delete runtime release."""
    get_client().runtime.delete(cid)


@mcp.tool()
def execute_process(body: dict) -> dict:
    """Execute a process."""
    return get_client().execute.run(body)


@mcp.tool()
def cancel_execution(execution_id: str) -> None:
    """Cancel an execution."""
    get_client().execute.cancel(execution_id)