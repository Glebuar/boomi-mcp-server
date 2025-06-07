"""Helper functions for Boomi SDK interactions."""

from typing import Dict, Any, Optional
from boomi.models.atom_query_config import AtomQueryConfig
from boomi.models.environment_query_config import EnvironmentQueryConfig
from boomi.models.deployment_query_config import DeploymentQueryConfig
from boomi.models.packaged_component_query_config import PackagedComponentQueryConfig
from boomi.models.execution_record_query_config import ExecutionRecordQueryConfig
from boomi.models.query_filter import QueryFilter


def create_query_config(config_class, query_dict: Dict[str, Any]):
    """Convert MCP query dict to proper SDK config object."""
    try:
        if "QueryFilter" in query_dict:
            # Use the dict structure directly
            return config_class(query_filter=query_dict["QueryFilter"])
        else:
            # Handle direct expression format
            return config_class(query_filter={"expression": query_dict})
    except Exception as e:
        raise ValueError(f"Invalid query structure: {e}")


def extract_response_data(response) -> Dict[str, Any]:
    """Extract data from SDK response objects."""
    if hasattr(response, '__dict__'):
        if hasattr(response, '_kwargs') and response._kwargs:
            # Handle XML response format
            kwargs = response._kwargs
            if '{http://api.platform.boomi.com/}QueryResult' in kwargs:
                query_result = kwargs['{http://api.platform.boomi.com/}QueryResult']
                # Extract the actual results
                results = []
                for key, value in query_result.items():
                    if key.startswith('{') and key.endswith('}result'):
                        results = value if isinstance(value, list) else [value]
                        break
                
                return {
                    'result': results,
                    'numberOfResults': int(query_result.get('@numberOfResults', 0))
                }
            
            # Return the raw kwargs for other response types
            return kwargs
        
        # Return the object's dict if no _kwargs
        return response.__dict__
    
    # Return as-is if it's already a dict
    if isinstance(response, dict):
        return response
    
    # Convert to string if it's a simple type
    return {"result": str(response)}


# Query config creation helpers
def create_atom_query_config(query: Dict[str, Any]) -> AtomQueryConfig:
    """Create AtomQueryConfig from MCP query dict."""
    return create_query_config(AtomQueryConfig, query)


def create_environment_query_config(query: Dict[str, Any]) -> EnvironmentQueryConfig:
    """Create EnvironmentQueryConfig from MCP query dict."""
    return create_query_config(EnvironmentQueryConfig, query)


def create_deployment_query_config(query: Dict[str, Any]) -> DeploymentQueryConfig:
    """Create DeploymentQueryConfig from MCP query dict."""
    return create_query_config(DeploymentQueryConfig, query)


def create_execution_record_query_config(query: Dict[str, Any]) -> ExecutionRecordQueryConfig:
    """Create ExecutionRecordQueryConfig from MCP query dict."""
    return create_query_config(ExecutionRecordQueryConfig, query)


def create_packaged_component_query_config(query: Dict[str, Any]) -> PackagedComponentQueryConfig:
    """Create PackagedComponentQueryConfig from MCP query dict."""
    return create_query_config(PackagedComponentQueryConfig, query)