"""
Result Formatting Utilities

Handles truncation, pagination, and summarization of large result sets.
Ensures MCP responses remain manageable for AI consumption.
"""

from typing import List, Dict, Any, Optional, Callable


def format_large_result(
    items: List[Any],
    limit: int = 100,
    total_count: Optional[int] = None,
    item_formatter: Optional[Callable[[Any], Dict]] = None
) -> Dict[str, Any]:
    """
    Truncate and summarize large result sets.

    Args:
        items: List of result items
        limit: Maximum number of items to return
        total_count: Total number of items available (if known)
        item_formatter: Optional function to format each item

    Returns:
        Formatted result with truncation info
    """
    if item_formatter:
        items = [item_formatter(item) for item in items]

    actual_count = total_count if total_count is not None else len(items)
    is_truncated = actual_count > limit

    if not is_truncated:
        return {
            "items": items,
            "count": len(items),
            "total": actual_count,
            "truncated": False
        }

    return {
        "items": items[:limit],
        "count": min(limit, len(items)),
        "total": actual_count,
        "truncated": True,
        "message": f"Showing {min(limit, len(items))} of {actual_count} results. Refine your query for specific results.",
        "hint": "Use filters to narrow down results (e.g., component_type, date_range, status, folder_name)."
    }


def handle_pagination(
    sdk_query_func: Callable,
    query_config: Any,
    max_results: int = 1000,
    page_size: Optional[int] = None
) -> List[Any]:
    """
    Automatically handle Boomi API pagination.

    Args:
        sdk_query_func: SDK query function (e.g., sdk.component.query_component)
        query_config: Query configuration object
        max_results: Maximum total results to retrieve
        page_size: Results per page (if SDK supports it)

    Returns:
        Combined results from all pages
    """
    all_results = []
    query_token = None

    while True:
        # Query with token if available (for pagination)
        if query_token:
            try:
                response = sdk_query_func(query_token=query_token)
            except TypeError:
                # SDK doesn't support query_token parameter, break
                break
        else:
            response = sdk_query_func(query_config)

        # Handle different response formats
        if hasattr(response, 'result'):
            results = response.result
        elif isinstance(response, list):
            results = response
        elif isinstance(response, dict) and 'result' in response:
            results = response['result']
        else:
            results = [response]

        all_results.extend(results)

        # Stop conditions
        if len(all_results) >= max_results:
            break

        # Check for more pages
        if hasattr(response, 'query_token'):
            query_token = response.query_token
            if not query_token:
                break
        else:
            # No pagination support, break
            break

    return all_results[:max_results]


def summarize_list(
    items: List[Any],
    key_fields: List[str],
    max_items: int = 10
) -> Dict[str, Any]:
    """
    Create a summary of a list showing key fields only.

    Args:
        items: List of items to summarize
        key_fields: Fields to extract from each item
        max_items: Maximum items to include in summary

    Returns:
        Summary with key fields and stats
    """
    summary_items = []

    for item in items[:max_items]:
        summary_item = {}
        for field in key_fields:
            if isinstance(item, dict):
                summary_item[field] = item.get(field, None)
            elif hasattr(item, field):
                summary_item[field] = getattr(item, field, None)
        summary_items.append(summary_item)

    return {
        "summary": summary_items,
        "total_count": len(items),
        "showing": min(len(items), max_items),
        "truncated": len(items) > max_items
    }


def format_component_summary(component: Any) -> Dict[str, Any]:
    """
    Format a component into a concise summary.

    Args:
        component: Component object from SDK

    Returns:
        Summary dict with key fields
    """
    summary = {}

    # Extract common fields
    if hasattr(component, 'id_'):
        summary['id'] = component.id_
    elif hasattr(component, 'componentId'):
        summary['id'] = component.componentId
    elif isinstance(component, dict):
        summary['id'] = component.get('id') or component.get('componentId')

    if hasattr(component, 'name'):
        summary['name'] = component.name
    elif isinstance(component, dict):
        summary['name'] = component.get('name')

    if hasattr(component, 'type'):
        summary['type'] = component.type
    elif isinstance(component, dict):
        summary['type'] = component.get('type')

    if hasattr(component, 'folder_name'):
        summary['folder'] = component.folder_name
    elif isinstance(component, dict):
        summary['folder'] = component.get('folderName') or component.get('folder_name')

    return summary


def format_execution_summary(execution: Any) -> Dict[str, Any]:
    """
    Format an execution record into a concise summary.

    Args:
        execution: Execution record from SDK

    Returns:
        Summary dict with key fields
    """
    summary = {}

    if hasattr(execution, 'execution_id'):
        summary['execution_id'] = execution.execution_id
    elif isinstance(execution, dict):
        summary['execution_id'] = execution.get('executionId') or execution.get('execution_id')

    if hasattr(execution, 'status'):
        summary['status'] = execution.status
    elif isinstance(execution, dict):
        summary['status'] = execution.get('status')

    if hasattr(execution, 'process_name'):
        summary['process'] = execution.process_name
    elif isinstance(execution, dict):
        summary['process'] = execution.get('processName') or execution.get('process_name')

    if hasattr(execution, 'start_time'):
        summary['started'] = execution.start_time
    elif isinstance(execution, dict):
        summary['started'] = execution.get('startTime') or execution.get('start_time')

    if hasattr(execution, 'error_message'):
        summary['error'] = execution.error_message
    elif isinstance(execution, dict):
        summary['error'] = execution.get('errorMessage') or execution.get('error_message')

    return summary
