# Boomi SDK vs MCP Server Tools Comparison

## Overview
The MCP server tools are using a client abstraction that doesn't match the actual Boomi SDK structure. The SDK uses a different API pattern than what the MCP tools expect.

## SDK Services Available

Based on the Boomi SDK (`/home/gleb/boomi/boomi-python/src/boomi/sdk.py`), the following services are available:

### Account Management
- `account` - AccountService
- `account_cloud_attachment_properties` - AccountCloudAttachmentPropertiesService
- `account_cloud_attachment_quota` - AccountCloudAttachmentQuotaService
- `account_group` - AccountGroupService
- `account_group_account` - AccountGroupAccountService
- `account_group_integration_pack` - AccountGroupIntegrationPackService
- `account_group_user_role` - AccountGroupUserRoleService
- `account_provision` - AccountProvisionService
- `account_sso_config` - AccountSsoConfigService
- `account_user_federation` - AccountUserFederationService
- `account_user_role` - AccountUserRoleService

### API Usage & Monitoring
- `api_usage_count` - ApiUsageCountService
- `audit_log` - AuditLogService
- `event` - EventService
- `throughput_account` - ThroughputAccountService
- `throughput_account_group` - ThroughputAccountGroupService

### Atom Management
- `atom` - AtomService
- `atom_as2_artifacts` - AtomAs2ArtifactsService
- `atom_connection_field_extension_summary` - AtomConnectionFieldExtensionSummaryService
- `atom_connector_versions` - AtomConnectorVersionsService
- `atom_counters` - AtomCountersService
- `atom_disk_space` - AtomDiskSpaceService
- `atom_log` - AtomLogService
- `atom_purge` - AtomPurgeService
- `atom_security_policies` - AtomSecurityPoliciesService
- `atom_startup_properties` - AtomStartupPropertiesService
- `atom_worker_log` - AtomWorkerLogService

### Component Management
- `component` - ComponentService
- `component_atom_attachment` - ComponentAtomAttachmentService
- `component_diff_request` - ComponentDiffRequestService
- `component_environment_attachment` - ComponentEnvironmentAttachmentService
- `component_metadata` - ComponentMetadataService
- `component_reference` - ComponentReferenceService
- `organization_component` - OrganizationComponentService
- `packaged_component` - PackagedComponentService
- `packaged_component_manifest` - PackagedComponentManifestService

### Connector Records
- `as2_connector_record` - As2ConnectorRecordService
- `edi_custom_connector_record` - EdiCustomConnectorRecordService
- `edifact_connector_record` - EdifactConnectorRecordService
- `generic_connector_record` - GenericConnectorRecordService
- `hl7_connector_record` - Hl7ConnectorRecordService
- `odette_connector_record` - OdetteConnectorRecordService
- `oftp2_connector_record` - Oftp2ConnectorRecordService
- `rosetta_net_connector_record` - RosettaNetConnectorRecordService
- `tradacoms_connector_record` - TradacomsConnectorRecordService
- `x12_connector_record` - X12ConnectorRecordService

### Deployment & Environment
- `cloud` - CloudService
- `deployed_expired_certificate` - DeployedExpiredCertificateService
- `deployed_package` - DeployedPackageService
- `deployment` - DeploymentService
- `environment` - EnvironmentService
- `environment_atom_attachment` - EnvironmentAtomAttachmentService
- `environment_connection_field_extension_summary` - EnvironmentConnectionFieldExtensionSummaryService
- `environment_extensions` - EnvironmentExtensionsService
- `environment_map_extension` - EnvironmentMapExtensionService
- `environment_map_extension_external_component` - EnvironmentMapExtensionExternalComponentService
- `environment_map_extension_user_defined_function` - EnvironmentMapExtensionUserDefinedFunctionService
- `environment_map_extension_user_defined_function_summary` - EnvironmentMapExtensionUserDefinedFunctionSummaryService
- `environment_map_extensions_summary` - EnvironmentMapExtensionsSummaryService
- `environment_role` - EnvironmentRoleService

### Execution & Process Management
- `cancel_execution` - CancelExecutionService
- `execute_process` - ExecuteProcessService
- `execution_artifacts` - ExecutionArtifactsService
- `execution_connector` - ExecutionConnectorService
- `execution_count_account` - ExecutionCountAccountService
- `execution_count_account_group` - ExecutionCountAccountGroupService
- `execution_record` - ExecutionRecordService
- `execution_request` - ExecutionRequestService
- `execution_summary_record` - ExecutionSummaryRecordService
- `process` - ProcessService
- `process_atom_attachment` - ProcessAtomAttachmentService
- `process_environment_attachment` - ProcessEnvironmentAttachmentService
- `process_log` - ProcessLogService
- `process_schedule_status` - ProcessScheduleStatusService
- `process_schedules` - ProcessSchedulesService
- `persisted_process_properties` - PersistedProcessPropertiesService
- `rerun_document` - RerunDocumentService

### Integration Pack Management
- `integration_pack` - IntegrationPackService
- `integration_pack_atom_attachment` - IntegrationPackAtomAttachmentService
- `integration_pack_environment_attachment` - IntegrationPackEnvironmentAttachmentService
- `integration_pack_instance` - IntegrationPackInstanceService
- `publisher_integration_pack` - PublisherIntegrationPackService
- `release_integration_pack` - ReleaseIntegrationPackService
- `release_integration_pack_status` - ReleaseIntegrationPackStatusService

### Other Services
- `branch` - BranchService
- `change_listener_status` - ChangeListenerStatusService
- `clear_queue` - ClearQueueService
- `connection_licensing_report` - ConnectionLicensingReportService
- `connector` - ConnectorService
- `connector_document` - ConnectorDocumentService
- `custom_tracked_field` - CustomTrackedFieldService
- `document_count_account` - DocumentCountAccountService
- `document_count_account_group` - DocumentCountAccountGroupService
- `folder` - FolderService
- `get_assignable_roles` - GetAssignableRolesService
- `installer_token` - InstallerTokenService
- `java_rollback` - JavaRollbackService
- `java_upgrade` - JavaUpgradeService
- `list_queues` - ListQueuesService
- `listener_status` - ListenerStatusService
- `merge_request` - MergeRequestService
- `move_queue_request` - MoveQueueRequestService
- `node_offboard` - NodeOffboardService
- `refresh_secrets_manager` - RefreshSecretsManagerService
- `role` - RoleService
- `runtime_release_schedule` - RuntimeReleaseScheduleService
- `runtime_restart_request` - RuntimeRestartRequestService
- `shared_communication_channel_component` - SharedCommunicationChannelComponentService
- `shared_server_information` - SharedServerInformationService
- `shared_web_server` - SharedWebServerService
- `shared_web_server_log` - SharedWebServerLogService
- `trading_partner_component` - TradingPartnerComponentService
- `trading_partner_processing_group` - TradingPartnerProcessingGroupService
- `worker` - WorkerService

## SDK Service Methods

Based on inspection of service files, common methods include:
- `create_[resource]()` - Create a new resource
- `get_[resource]()` - Get a resource by ID
- `update_[resource]()` - Update an existing resource
- `delete_[resource]()` - Delete a resource (not all services have this)
- `query_[resource]()` - Query/search for resources
- `query_more_[resource]()` - Continue a paginated query
- `bulk_[resource]()` - Bulk operations

## MCP Tools Currently Defined

The MCP server defines these tools:

### Component Management
- `create_component(xml_path)` - Uses `get_client().components.create()`
- `update_component(component_id, xml)` - Uses `get_client().components.update()`
- `delete_component(component_id)` - Uses `get_client().components.delete()`
- `get_component(component_id)` - Uses `get_client().components.get()`

### Package & Deployment
- `create_package(component_id, package_version, notes)` - Uses `get_client().packages.create()`
- `deploy_package(environment_id, package_id)` - Uses `get_client().deployments.deploy()`

### Folder Management
- `create_folder(name, parent_id)` - Uses `get_client().folders.create()`
- `get_folder(folder_id)` - Uses `get_client().folders.get()`
- `delete_folder(folder_id)` - Uses `get_client().folders.delete()`

### Environment & Atom
- `list_atoms()` - Uses `get_client().atoms.list()`
- `list_environments()` - Uses `get_client().environments.list()`

### Execution & Runs
- `query_runs(query)` - Uses `get_client().runs.list()`
- `get_run_log(execution_id)` - Uses `get_client().runs.log()`
- `query_runs_more(token)` - Uses `get_client().runs.list_more()`
- `query_run_summary(query)` - Uses `get_client().runs.summary()`
- `query_run_summary_more(token)` - Uses `get_client().runs.summary_more()`
- `query_run_connectors(query)` - Uses `get_client().runs.connectors()`
- `query_run_connectors_more(token)` - Uses `get_client().runs.connectors_more()`
- `query_execution_count_account(query)` - Uses `get_client().runs.count_account()`
- `query_execution_count_account_more(token)` - Uses `get_client().runs.count_account_more()`
- `query_execution_count_group(query)` - Uses `get_client().runs.count_group()`
- `query_execution_count_group_more(token)` - Uses `get_client().runs.count_group_more()`
- `get_run_artifacts(execution_id)` - Uses `get_client().runs.artifacts()`
- `request_execution(body)` - Uses `get_client().runs.request()`
- `get_run_document(generic_id)` - Uses `get_client().runs.doc()`
- `query_run_documents(query)` - Uses `get_client().runs.docs()`
- `query_run_documents_more(token)` - Uses `get_client().runs.docs_more()`

### Connector Records
- `query_as2_records(query)` - Uses `get_client().runs.as2_records()`
- `query_as2_records_more(token)` - Uses `get_client().runs.as2_records_more()`
- `query_edicustom_records(query)` - Uses `get_client().runs.edicustom_records()`
- `query_edicustom_records_more(token)` - Uses `get_client().runs.edicustom_records_more()`
- `query_edifact_records(query)` - Uses `get_client().runs.edifact_records()`
- `query_edifact_records_more(token)` - Uses `get_client().runs.edifact_records_more()`
- `query_hl7_records(query)` - Uses `get_client().runs.hl7_records()`
- `query_hl7_records_more(token)` - Uses `get_client().runs.hl7_records_more()`
- `query_odette_records(query)` - Uses `get_client().runs.odette_records()`
- `query_odette_records_more(token)` - Uses `get_client().runs.odette_records_more()`
- `query_oftp2_records(query)` - Uses `get_client().runs.oftp2_records()`
- `query_oftp2_records_more(token)` - Uses `get_client().runs.oftp2_records_more()`
- `query_rosetta_records(query)` - Uses `get_client().runs.rosetta_records()`
- `query_rosetta_records_more(token)` - Uses `get_client().runs.rosetta_records_more()`
- `query_tradacoms_records(query)` - Uses `get_client().runs.tradacoms_records()`
- `query_tradacoms_records_more(token)` - Uses `get_client().runs.tradacoms_records_more()`
- `query_x12_records(query)` - Uses `get_client().runs.x12_records()`
- `query_x12_records_more(token)` - Uses `get_client().runs.x12_records_more()`

### Logs & Auditing
- `get_atom_log(body)` - Uses `get_client().runs.atom_log()`
- `get_as2_artifacts(body)` - Uses `get_client().runs.as2_artifacts()`
- `get_worker_log(body)` - Uses `get_client().runs.worker_log()`
- `get_audit_log(audit_id)` - Uses `get_client().runs.audit()`
- `query_audit_logs(query)` - Uses `get_client().runs.audit_query()`
- `query_audit_logs_more(token)` - Uses `get_client().runs.audit_query_more()`

### Events
- `query_events(query)` - Uses `get_client().runs.events()`
- `query_events_more(token)` - Uses `get_client().runs.events_more()`

### Schedules
- `get_schedule(schedule_id)` - Uses `get_client().schedules.get()`
- `update_schedule(schedule_id, body)` - Uses `get_client().schedules.update()`
- `query_schedules(query)` - Uses `get_client().schedules.query()`
- `bulk_schedules(ids)` - Uses `get_client().schedules.bulk()`

### Extensions
- `get_extensions(environment_id)` - Uses `get_client().extensions.get()`
- `update_extensions(environment_id, body)` - Uses `get_client().extensions.update()`
- `query_extensions(query)` - Uses `get_client().extensions.query()`
- `query_extension_field_summary(query)` - Uses `get_client().extensions.query_conn_field_summary()`

### Runtime
- `create_runtime_release(body)` - Uses `get_client().runtime.create()`
- `get_runtime_release(cid)` - Uses `get_client().runtime.get()`
- `update_runtime_release(cid, body)` - Uses `get_client().runtime.update()`
- `delete_runtime_release(cid)` - Uses `get_client().runtime.delete()`

### Execution
- `execute_process(body)` - Uses `get_client().execute.run()`
- `cancel_execution(execution_id)` - Uses `get_client().execute.cancel()`

## Key Issues

1. **Authentication Mismatch**: 
   - MCP auth expects: `Boomi(account=..., user=..., secret=...)`
   - SDK expects: `Boomi(username=..., password=..., account_id=...)`

2. **API Structure Mismatch**:
   - MCP expects: `client.components.create()`, `client.folders.get()`, etc.
   - SDK provides: `client.component.create_component()`, `client.folder.get_folder()`, etc.

3. **Missing Client Abstraction**:
   - The MCP tools expect a client wrapper with nested objects (components, folders, runs, etc.)
   - The SDK provides flat service objects directly on the Boomi instance

## SDK Methods Missing from MCP Tools

Many SDK services are not exposed through MCP tools:
- Account management services
- Cloud attachment services
- Integration pack services
- Trading partner services
- Java upgrade/rollback services
- Node offboarding
- Queue management (clear_queue, move_queue_request)
- Listener status management
- Many connector-specific services
- Branch management
- Merge requests
- Role management
- Worker management

## MCP Tools That Don't Match SDK

The MCP tools use a client abstraction that doesn't exist in the SDK:
- All `get_client().xxx.yyy()` calls need to be mapped to actual SDK service methods
- The nested structure (components, folders, runs, etc.) needs to be created or the tools need to be rewritten

## Recommendations

1. **Create a Client Wrapper**: Build an abstraction layer that maps the expected MCP interface to the actual SDK methods
2. **Update MCP Tools**: Rewrite the tools to use the SDK directly without the abstraction layer
3. **Add Missing Tools**: Implement MCP tools for the many SDK services that are currently not exposed
4. **Fix Authentication**: Update the auth module to properly initialize the SDK with the correct parameters