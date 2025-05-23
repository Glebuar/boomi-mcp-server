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
def health_check() -> bool:
    """Simple connectivity check returning ``True`` when the server is alive."""
    return True


@mcp.tool()
def create_component(xml_path: str) -> dict:
    """Create a new component in Boomi from the provided XML definition."""
    boomi = get_client()
    comp = boomi.components.create(Path(xml_path))
    return comp.model_dump()


@mcp.tool()
def update_component(component_id: str, xml: str) -> None:
    """Replace the XML configuration for an existing component."""
    get_client().components.update(component_id, xml)


@mcp.tool()
def delete_component(component_id: str) -> None:
    """Remove a component from the account using its ID."""
    get_client().components.delete(component_id)


@mcp.tool()
def get_component(component_id: str) -> dict:
    """Retrieve a component's metadata and XML by ID."""
    return get_client().components.get(component_id).model_dump()


@mcp.tool()
def create_package(component_id: str, package_version: str | None = None,
                    notes: str | None = None) -> dict:
    """Package a component for deployment, optionally setting a version."""
    return get_client().packages.create(component_id, package_version, notes)


@mcp.tool()
def deploy_package(environment_id: str, package_id: str) -> dict:
    """Deploy a previously created package to an environment."""
    return get_client().deployments.deploy(environment_id, package_id)


@mcp.tool()
def create_folder(name: str, parent_id: str | None = None) -> dict:
    """Create a new folder optionally under ``parent_id``."""
    return get_client().folders.create(name, parent_id)


@mcp.tool()
def get_folder(folder_id: str) -> dict:
    """Return folder details for the given ID."""
    return get_client().folders.get(folder_id)


@mcp.tool()
def delete_folder(folder_id: str) -> None:
    """Delete an existing folder by ID."""
    get_client().folders.delete(folder_id)


@mcp.tool()
def list_atoms() -> list:
    """List all atoms available to the account."""
    return get_client().atoms.list()


@mcp.tool()
def list_environments() -> list:
    """List all deployment environments in the connected Boomi account."""
    return get_client().environments.list()


@mcp.tool()
def query_runs(query: dict) -> dict:
    """Search for execution records matching the provided query."""
    return get_client().runs.list(query)


@mcp.tool()
def get_run_log(execution_id: str) -> str:
    """Return a URL pointing to the log for the given execution."""
    return get_client().runs.log(execution_id)


@mcp.tool()
def query_runs_more(token: str) -> dict:
    """Continue a previous execution query using the pagination token."""
    return get_client().runs.list_more(token)


@mcp.tool()
def query_run_summary(query: dict) -> dict:
    """Retrieve summarized statistics for executions matching a query."""
    return get_client().runs.summary(query)


@mcp.tool()
def query_run_summary_more(token: str) -> dict:
    """Fetch additional summary records using a query token."""
    return get_client().runs.summary_more(token)


@mcp.tool()
def query_run_connectors(query: dict) -> dict:
    """Query execution connector records."""
    return get_client().runs.connectors(query)


@mcp.tool()
def query_run_connectors_more(token: str) -> dict:
    """Fetch additional connector records using a query token."""
    return get_client().runs.connectors_more(token)


@mcp.tool()
def query_execution_count_account(query: dict) -> dict:
    """Query execution count by account."""
    return get_client().runs.count_account(query)


@mcp.tool()
def query_execution_count_account_more(token: str) -> dict:
    """Fetch additional account counts using a query token."""
    return get_client().runs.count_account_more(token)


@mcp.tool()
def query_execution_count_group(query: dict) -> dict:
    """Query execution count by account group."""
    return get_client().runs.count_group(query)


@mcp.tool()
def query_execution_count_group_more(token: str) -> dict:
    """Fetch additional group counts using a query token."""
    return get_client().runs.count_group_more(token)


@mcp.tool()
def get_run_artifacts(execution_id: str) -> str:
    """Get a URL to execution artifacts."""
    return get_client().runs.artifacts(execution_id)


@mcp.tool()
def request_execution(body: dict) -> dict:
    """Submit an execution request."""
    return get_client().runs.request(body)


@mcp.tool()
def get_run_document(generic_id: str) -> dict:
    """Fetch a generic connector record by ID."""
    return get_client().runs.doc(generic_id)


@mcp.tool()
def query_run_documents(query: dict) -> dict:
    """Query generic connector records."""
    return get_client().runs.docs(query)


@mcp.tool()
def query_run_documents_more(token: str) -> dict:
    """Fetch additional generic records using a query token."""
    return get_client().runs.docs_more(token)


@mcp.tool()
def query_as2_records(query: dict) -> dict:
    """Query AS2 connector records."""
    return get_client().runs.as2_records(query)


@mcp.tool()
def query_as2_records_more(token: str) -> dict:
    """Fetch additional AS2 records using a query token."""
    return get_client().runs.as2_records_more(token)


@mcp.tool()
def query_edicustom_records(query: dict) -> dict:
    """Query EDI Custom connector records."""
    return get_client().runs.edicustom_records(query)


@mcp.tool()
def query_edicustom_records_more(token: str) -> dict:
    """Fetch additional EDI Custom records using a query token."""
    return get_client().runs.edicustom_records_more(token)


@mcp.tool()
def query_edifact_records(query: dict) -> dict:
    """Query EDIFACT connector records."""
    return get_client().runs.edifact_records(query)


@mcp.tool()
def query_edifact_records_more(token: str) -> dict:
    """Fetch additional EDIFACT records using a query token."""
    return get_client().runs.edifact_records_more(token)


@mcp.tool()
def query_hl7_records(query: dict) -> dict:
    """Query HL7 connector records."""
    return get_client().runs.hl7_records(query)


@mcp.tool()
def query_hl7_records_more(token: str) -> dict:
    """Fetch additional HL7 records using a query token."""
    return get_client().runs.hl7_records_more(token)


@mcp.tool()
def query_odette_records(query: dict) -> dict:
    """Query ODETTE connector records."""
    return get_client().runs.odette_records(query)


@mcp.tool()
def query_odette_records_more(token: str) -> dict:
    """Fetch additional ODETTE records using a query token."""
    return get_client().runs.odette_records_more(token)


@mcp.tool()
def query_oftp2_records(query: dict) -> dict:
    """Query OFTP2 connector records."""
    return get_client().runs.oftp2_records(query)


@mcp.tool()
def query_oftp2_records_more(token: str) -> dict:
    """Fetch additional OFTP2 records using a query token."""
    return get_client().runs.oftp2_records_more(token)


@mcp.tool()
def query_rosetta_records(query: dict) -> dict:
    """Query RosettaNet connector records."""
    return get_client().runs.rosetta_records(query)


@mcp.tool()
def query_rosetta_records_more(token: str) -> dict:
    """Fetch additional RosettaNet records using a query token."""
    return get_client().runs.rosetta_records_more(token)


@mcp.tool()
def query_tradacoms_records(query: dict) -> dict:
    """Query Tradacoms connector records."""
    return get_client().runs.tradacoms_records(query)


@mcp.tool()
def query_tradacoms_records_more(token: str) -> dict:
    """Fetch additional Tradacoms records using a query token."""
    return get_client().runs.tradacoms_records_more(token)


@mcp.tool()
def query_x12_records(query: dict) -> dict:
    """Query X12 connector records."""
    return get_client().runs.x12_records(query)


@mcp.tool()
def query_x12_records_more(token: str) -> dict:
    """Fetch additional X12 records using a query token."""
    return get_client().runs.x12_records_more(token)


@mcp.tool()
def get_atom_log(body: dict) -> str:
    """Get a URL to an atom log."""
    return get_client().runs.atom_log(body)


@mcp.tool()
def get_as2_artifacts(body: dict) -> str:
    """Get a URL to AS2 artifacts."""
    return get_client().runs.as2_artifacts(body)


@mcp.tool()
def get_worker_log(body: dict) -> str:
    """Get a URL to a worker log."""
    return get_client().runs.worker_log(body)


@mcp.tool()
def get_audit_log(audit_id: str) -> dict:
    """Fetch an audit log entry."""
    return get_client().runs.audit(audit_id)


@mcp.tool()
def query_audit_logs(query: dict) -> dict:
    """Query audit logs."""
    return get_client().runs.audit_query(query)


@mcp.tool()
def query_audit_logs_more(token: str) -> dict:
    """Fetch additional audit logs using a query token."""
    return get_client().runs.audit_query_more(token)


@mcp.tool()
def query_events(query: dict) -> dict:
    """Query events."""
    return get_client().runs.events(query)


@mcp.tool()
def query_events_more(token: str) -> dict:
    """Fetch additional events using a query token."""
    return get_client().runs.events_more(token)


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
