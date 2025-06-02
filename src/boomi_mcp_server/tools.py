from fastmcp import FastMCP
from .auth import get_client
from typing import Optional, Dict, Any, List

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


# Component Management Tools
@mcp.tool()
def create_component(xml_path: str) -> dict:
    """Create a new component in Boomi from the provided XML definition."""
    boomi = get_client()
    with open(xml_path, 'r') as f:
        xml_content = f.read()
    return boomi.component.create_component(xml_content)


@mcp.tool()
def update_component(component_id: str, xml: str) -> dict:
    """Replace the XML configuration for an existing component."""
    return get_client().component.update_component(component_id, xml)


@mcp.tool()
def get_component(component_id: str) -> dict:
    """Retrieve a component's metadata and XML by ID."""
    return get_client().component.get_component(component_id)


@mcp.tool()
def query_components(query: dict) -> dict:
    """Search for components by name, type, or folder.
    
    Example query:
    {
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {
                        "property": "name",
                        "operator": "LIKE",
                        "argument": ["MyProcess%"]
                    }
                ]
            }
        }
    }
    """
    return get_client().component.query_component(query)


# Package Management Tools
@mcp.tool()
def create_package(component_id: str, package_version: Optional[str] = None,
                    notes: Optional[str] = None) -> dict:
    """Package a component for deployment, optionally setting a version."""
    package_data = {"componentId": component_id}
    if package_version:
        package_data["packageVersion"] = package_version
    if notes:
        package_data["notes"] = notes
    return get_client().packaged_component.create_packaged_component(package_data)


@mcp.tool()
def get_package(package_id: str) -> dict:
    """Get details of a packaged component."""
    return get_client().packaged_component.get_packaged_component(package_id)


@mcp.tool()
def query_packages(query: dict) -> dict:
    """Query packaged components."""
    return get_client().packaged_component.query_packaged_component(query)


# Deployment Management Tools
@mcp.tool()
def deploy_package(environment_id: str, package_id: str, notes: Optional[str] = None) -> dict:
    """Deploy a previously created package to an environment."""
    deployment_data = {
        "environmentId": environment_id,
        "packagedComponentId": package_id
    }
    if notes:
        deployment_data["notes"] = notes
    return get_client().deployment.create_deployment(deployment_data)


@mcp.tool()
def get_deployment(deployment_id: str) -> dict:
    """Check deployment status and details."""
    return get_client().deployment.get_deployment(deployment_id)


@mcp.tool()
def query_deployments(query: dict) -> dict:
    """Query deployments by environment or component.
    
    Example query:
    {
        "QueryFilter": {
            "expression": {
                "property": "environmentId",
                "operator": "EQUALS",
                "argument": ["env-id-here"]
            }
        }
    }
    """
    return get_client().deployment.query_deployment(query)


@mcp.tool()
def query_deployed_packages(query: dict) -> dict:
    """Query deployed packages in environments."""
    return get_client().deployed_package.query_deployed_package(query)


# Folder Management Tools
@mcp.tool()
def create_folder(name: str, parent_id: Optional[str] = None) -> dict:
    """Create a new folder optionally under ``parent_id``."""
    folder_data = {"name": name}
    if parent_id:
        folder_data["parentId"] = parent_id
    return get_client().folder.create_folder(folder_data)


@mcp.tool()
def get_folder(folder_id: str) -> dict:
    """Return folder details for the given ID."""
    return get_client().folder.get_folder(folder_id)


@mcp.tool()
def delete_folder(folder_id: str) -> dict:
    """Delete an existing folder by ID."""
    return get_client().folder.delete_folder(folder_id)


# Environment and Atom Management Tools
@mcp.tool()
def query_environments(query: dict) -> dict:
    """Query deployment environments.
    
    Example query:
    {
        "QueryFilter": {
            "expression": {
                "property": "name",
                "operator": "LIKE",
                "argument": ["%Production%"]
            }
        }
    }
    """
    return get_client().environment.query_environment(query)


@mcp.tool()
def get_environment(environment_id: str) -> dict:
    """Get details for a specific environment by ID."""
    return get_client().environment.get_environment(environment_id)


@mcp.tool()
def query_atoms(query: dict) -> dict:
    """Query atoms in the account.
    
    Example query:
    {
        "QueryFilter": {
            "expression": {
                "property": "status",
                "operator": "EQUALS",
                "argument": ["ONLINE"]
            }
        }
    }
    """
    return get_client().atom.query_atom(query)


@mcp.tool()
def get_atom(atom_id: str) -> dict:
    """Get details for a specific atom by ID."""
    return get_client().atom.get_atom(atom_id)


# Process Attachment Tools (Critical for execution)
@mcp.tool()
def attach_process_to_atom(process_id: str, atom_id: str) -> dict:
    """Attach a process to an atom for execution."""
    attachment_data = {
        "processId": process_id,
        "atomId": atom_id
    }
    return get_client().process_atom_attachment.create_process_atom_attachment(attachment_data)


@mcp.tool()
def detach_process_from_atom(process_id: str, atom_id: str) -> dict:
    """Detach a process from an atom."""
    return get_client().process_atom_attachment.delete_process_atom_attachment(process_id, atom_id)


@mcp.tool()
def query_process_attachments(query: dict) -> dict:
    """Query process-atom attachments."""
    return get_client().process_atom_attachment.query_process_atom_attachment(query)


# Environment Attachment Tools
@mcp.tool()
def attach_environment_to_atom(environment_id: str, atom_id: str) -> dict:
    """Attach an environment to an atom."""
    attachment_data = {
        "environmentId": environment_id,
        "atomId": atom_id
    }
    return get_client().environment_atom_attachment.create_environment_atom_attachment(attachment_data)


@mcp.tool()
def query_environment_attachments(query: dict) -> dict:
    """Query environment-atom attachments."""
    return get_client().environment_atom_attachment.query_environment_atom_attachment(query)


# Execution Tools
@mcp.tool()
def execute_process(process_id: str, atom_id: str, process_properties: Optional[Dict[str, Any]] = None) -> dict:
    """Execute a process on a specific atom.
    
    Args:
        process_id: The ID of the process to execute
        atom_id: The ID of the atom to execute on
        process_properties: Optional dict of process properties to pass
    """
    execution_data = {
        "processId": process_id,
        "atomId": atom_id
    }
    if process_properties:
        execution_data["processProperties"] = {
            "processProperty": [
                {"@name": k, "#text": v} for k, v in process_properties.items()
            ]
        }
    return get_client().execute_process.create_execute_process(execution_data)


@mcp.tool()
def cancel_execution(execution_id: str) -> dict:
    """Cancel a running execution."""
    return get_client().cancel_execution.create_cancel_execution({"executionId": execution_id})


@mcp.tool()
def request_execution(body: dict) -> dict:
    """Submit an execution request with custom configuration."""
    return get_client().execution_request.create_execution_request(body)


# Execution Monitoring Tools
@mcp.tool()
def query_executions(query: dict) -> dict:
    """Search for execution records matching the provided query.
    
    Example query:
    {
        "QueryFilter": {
            "expression": {
                "property": "processId",
                "operator": "EQUALS",
                "argument": ["process-id-here"]
            }
        }
    }
    """
    return get_client().execution_record.query_execution_record(query)


@mcp.tool()
def query_executions_more(token: str) -> dict:
    """Continue a previous execution query using the pagination token."""
    return get_client().execution_record.query_more_execution_record(token)


@mcp.tool()
def get_execution_log(execution_id: str) -> dict:
    """Return a URL pointing to the log for the given execution."""
    log_request = {"executionId": execution_id}
    return get_client().process_log.create_process_log(log_request)


@mcp.tool()
def query_execution_summary(query: dict) -> dict:
    """Retrieve summarized statistics for executions matching a query."""
    return get_client().execution_summary_record.query_execution_summary_record(query)


@mcp.tool()
def query_execution_summary_more(token: str) -> dict:
    """Fetch additional summary records using a query token."""
    return get_client().execution_summary_record.query_more_execution_summary_record(token)


@mcp.tool()
def get_execution_artifacts(execution_id: str) -> dict:
    """Get execution artifacts including request/response data."""
    artifact_request = {"executionId": execution_id}
    return get_client().execution_artifacts.create_execution_artifacts(artifact_request)


# Process Properties Management
@mcp.tool()
def get_process_properties(process_id: str, environment_id: str) -> dict:
    """Get process properties for a specific environment."""
    return get_client().persisted_process_properties.get_persisted_process_properties(
        process_id, environment_id
    )


@mcp.tool()
def update_process_properties(process_id: str, environment_id: str, properties: dict) -> dict:
    """Update process properties for a specific environment.
    
    Args:
        process_id: The process ID
        environment_id: The environment ID
        properties: Dict of property names and values
    """
    property_data = {
        "processId": process_id,
        "environmentId": environment_id,
        "processProperties": {
            "processProperty": [
                {"@name": k, "#text": v} for k, v in properties.items()
            ]
        }
    }
    return get_client().persisted_process_properties.update_persisted_process_properties(
        process_id, environment_id, property_data
    )


# Connector Management Tools
@mcp.tool()
def get_connector(connector_id: str) -> dict:
    """Get connector configuration details."""
    return get_client().connector.get_connector(connector_id)


@mcp.tool()
def update_connector(connector_id: str, connector_xml: str) -> dict:
    """Update connector configuration."""
    return get_client().connector.update_connector(connector_id, connector_xml)


@mcp.tool()
def query_connectors(query: dict) -> dict:
    """Query connectors in the account."""
    return get_client().connector.query_connector(query)


# Document/Data Flow Tools
@mcp.tool()
def rerun_document(document_id: str, execution_id: str) -> dict:
    """Rerun a failed document through a process."""
    rerun_data = {
        "documentId": document_id,
        "executionId": execution_id
    }
    return get_client().rerun_document.create_rerun_document(rerun_data)


# Queue Management Tools
@mcp.tool()
def list_queues(atom_id: str) -> dict:
    """List message queues on an atom."""
    queue_request = {"atomId": atom_id}
    return get_client().list_queues.create_list_queues(queue_request)


@mcp.tool()
def clear_queue(atom_id: str, queue_id: str) -> dict:
    """Clear messages from a queue."""
    clear_request = {
        "atomId": atom_id,
        "queueId": queue_id
    }
    return get_client().clear_queue.create_clear_queue(clear_request)


# Listener Management Tools
@mcp.tool()
def get_listener_status(atom_id: str, listener_id: str) -> dict:
    """Check listener status on an atom."""
    return get_client().listener_status.get_listener_status(atom_id, listener_id)


@mcp.tool()
def change_listener_status(atom_id: str, listener_id: str, action: str) -> dict:
    """Change listener status (START, STOP, RESTART).
    
    Args:
        atom_id: The atom ID
        listener_id: The listener ID
        action: One of "START", "STOP", or "RESTART"
    """
    status_data = {
        "atomId": atom_id,
        "listenerId": listener_id,
        "action": action
    }
    return get_client().change_listener_status.create_change_listener_status(status_data)


# Schedule Management Tools
@mcp.tool()
def get_schedule(schedule_id: str) -> dict:
    """Fetch schedule info."""
    return get_client().process_schedules.get_process_schedules(schedule_id)


@mcp.tool()
def update_schedule(schedule_id: str, schedule_data: dict) -> dict:
    """Update a schedule."""
    return get_client().process_schedules.update_process_schedules(schedule_id, schedule_data)


@mcp.tool()
def query_schedules(query: dict) -> dict:
    """Query schedules."""
    return get_client().process_schedules.query_process_schedules(query)


# Environment Extensions Tools
@mcp.tool()
def get_environment_extensions(environment_id: str) -> dict:
    """Get environment extensions."""
    return get_client().environment_extensions.get_environment_extensions(environment_id)


@mcp.tool()
def update_environment_extensions(environment_id: str, extensions_data: dict) -> dict:
    """Update environment extensions."""
    return get_client().environment_extensions.update_environment_extensions(
        environment_id, extensions_data
    )


@mcp.tool()
def query_environment_extensions(query: dict) -> dict:
    """Query environment extensions."""
    return get_client().environment_extensions.query_environment_extensions(query)


# Audit and Event Tools
@mcp.tool()
def get_audit_log(audit_id: str) -> dict:
    """Fetch an audit log entry."""
    return get_client().audit_log.get_audit_log(audit_id)


@mcp.tool()
def query_audit_logs(query: dict) -> dict:
    """Query audit logs."""
    return get_client().audit_log.query_audit_log(query)


@mcp.tool()
def query_audit_logs_more(token: str) -> dict:
    """Fetch additional audit logs using a query token."""
    return get_client().audit_log.query_more_audit_log(token)


@mcp.tool()
def query_events(query: dict) -> dict:
    """Query system events."""
    return get_client().event.query_event(query)


@mcp.tool()
def query_events_more(token: str) -> dict:
    """Fetch additional events using a query token."""
    return get_client().event.query_more_event(token)


# Atom Log Tools
@mcp.tool()
def get_atom_log(atom_id: str, log_date: str) -> dict:
    """Get a URL to an atom log for a specific date.
    
    Args:
        atom_id: The atom ID
        log_date: Date in YYYY-MM-DD format
    """
    log_request = {
        "atomId": atom_id,
        "logDate": log_date
    }
    return get_client().atom_log.create_atom_log(log_request)


@mcp.tool()
def get_worker_log(atom_id: str, container_id: str, log_date: str) -> dict:
    """Get a URL to a worker log.
    
    Args:
        atom_id: The atom ID
        container_id: The container/worker ID
        log_date: Date in YYYY-MM-DD format
    """
    log_request = {
        "atomId": atom_id,
        "containerId": container_id,
        "logDate": log_date
    }
    return get_client().atom_worker_log.create_atom_worker_log(log_request)


# Connector Record Query Tools
@mcp.tool()
def query_execution_connectors(query: dict) -> dict:
    """Query execution connector records."""
    return get_client().execution_connector.query_execution_connector(query)


@mcp.tool()
def query_execution_connectors_more(token: str) -> dict:
    """Fetch additional connector records using a query token."""
    return get_client().execution_connector.query_more_execution_connector(token)


@mcp.tool()
def query_as2_records(query: dict) -> dict:
    """Query AS2 connector records."""
    return get_client().as2_mdn_record.query_as2_mdn_record(query)


@mcp.tool()
def query_as2_records_more(token: str) -> dict:
    """Fetch additional AS2 records using a query token."""
    return get_client().as2_mdn_record.query_more_as2_mdn_record(token)


@mcp.tool()
def get_as2_artifacts(record_id: str) -> dict:
    """Get AS2 artifacts for a specific record."""
    artifact_request = {"recordId": record_id}
    return get_client().as2_mdn_artifacts.create_as2_mdn_artifacts(artifact_request)


@mcp.tool()
def query_edi_x12_records(query: dict) -> dict:
    """Query X12 EDI connector records."""
    return get_client().edi_x12_record.query_edi_x12_record(query)


@mcp.tool()
def query_edi_x12_records_more(token: str) -> dict:
    """Fetch additional X12 records using a query token."""
    return get_client().edi_x12_record.query_more_edi_x12_record(token)


@mcp.tool()
def query_edi_edifact_records(query: dict) -> dict:
    """Query EDIFACT connector records."""
    return get_client().edi_edifact_record.query_edi_edifact_record(query)


@mcp.tool()
def query_edi_edifact_records_more(token: str) -> dict:
    """Fetch additional EDIFACT records using a query token."""
    return get_client().edi_edifact_record.query_more_edi_edifact_record(token)


@mcp.tool()
def query_hl7_records(query: dict) -> dict:
    """Query HL7 connector records."""
    return get_client().hl7_record.query_hl7_record(query)


@mcp.tool()
def query_hl7_records_more(token: str) -> dict:
    """Fetch additional HL7 records using a query token."""
    return get_client().hl7_record.query_more_hl7_record(token)


# Account Information Tool
@mcp.tool()
def get_account_info() -> dict:
    """Get account information and settings."""
    return get_client().account.get()


# Component Metadata Tools
@mcp.tool()
def query_component_metadata(query: dict) -> dict:
    """Query component metadata to understand relationships."""
    return get_client().component_metadata.query_component_metadata(query)


# Runtime Management Tools
@mcp.tool()
def create_runtime_restart(atom_id: str, force_restart: bool = False) -> dict:
    """Request runtime restart for an atom.
    
    Args:
        atom_id: The atom to restart
        force_restart: Whether to force restart even if processes are running
    """
    restart_data = {
        "atomId": atom_id,
        "forceRestart": force_restart
    }
    return get_client().runtime_restart_request.create_runtime_restart_request(restart_data)