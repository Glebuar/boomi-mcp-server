"""
Error Handling Utilities

Standardized error response formatting for all MCP tools.
Provides user-friendly error messages with actionable hints.
"""

from typing import Dict, Optional, Any


def format_error_response(
    error_message: str,
    hint: Optional[str] = None,
    error_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a standardized error response.

    Args:
        error_message: Clear, user-friendly error description
        hint: Actionable suggestion for resolving the error
        error_type: Error category (authentication, permission, not_found, etc.)
        details: Additional error context

    Returns:
        Standardized error response dict
    """
    response = {
        "success": False,
        "error": error_message,
    }

    if hint:
        response["hint"] = hint

    if error_type:
        response["error_type"] = error_type

    if details:
        response["details"] = details

    return response


def handle_boomi_exception(e: Exception, context: str = "") -> Dict[str, Any]:
    """
    Convert Boomi SDK exceptions into user-friendly error responses.

    Args:
        e: Exception from Boomi SDK
        context: Additional context about what operation was being performed

    Returns:
        Formatted error response with hints
    """
    exception_name = type(e).__name__
    error_str = str(e)

    # Authentication errors
    if "authentication" in error_str.lower() or "unauthorized" in error_str.lower():
        return format_error_response(
            error_message="Authentication failed. Check your Boomi credentials.",
            hint="Use set_boomi_credentials to update your account credentials.",
            error_type="authentication",
            details={"context": context} if context else None
        )

    # Permission errors
    if "permission" in error_str.lower() or "forbidden" in error_str.lower() or "403" in error_str:
        return format_error_response(
            error_message="Permission denied. Insufficient privileges for this operation.",
            hint="Contact your Boomi administrator to grant necessary permissions.",
            error_type="permission",
            details={"context": context} if context else None
        )

    # Not found errors
    if "not found" in error_str.lower() or "404" in error_str:
        return format_error_response(
            error_message=f"Resource not found: {context}" if context else "Resource not found.",
            hint="Verify the ID is correct. Use query or list operations to find available resources.",
            error_type="not_found",
            details={"context": context} if context else None
        )

    # Already exists / conflict errors
    if "already exists" in error_str.lower() or "conflict" in error_str.lower() or "409" in error_str:
        return format_error_response(
            error_message=f"Resource already exists: {context}" if context else "Resource already exists.",
            hint="Use a different name or update the existing resource instead of creating a new one.",
            error_type="conflict",
            details={"context": context} if context else None
        )

    # Validation errors
    if "validation" in error_str.lower() or "invalid" in error_str.lower() or "400" in error_str:
        return format_error_response(
            error_message=f"Validation error: {error_str}",
            hint="Check that all required parameters are provided and have valid values. Use get_schema_template for expected format.",
            error_type="validation",
            details={"context": context} if context else None
        )

    # Rate limiting
    if "rate limit" in error_str.lower() or "429" in error_str:
        return format_error_response(
            error_message="Rate limit exceeded. Too many requests.",
            hint="Wait a few seconds and try again. Consider caching results for frequently accessed data.",
            error_type="rate_limit",
            details={"context": context} if context else None
        )

    # Timeout errors
    if "timeout" in error_str.lower() or "timed out" in error_str.lower():
        return format_error_response(
            error_message="Request timed out. The operation took too long to complete.",
            hint="Try again with a smaller query scope or check Boomi platform status.",
            error_type="timeout",
            details={"context": context} if context else None
        )

    # Connection errors
    if "connection" in error_str.lower() or "network" in error_str.lower():
        return format_error_response(
            error_message="Network connection error. Unable to reach Boomi API.",
            hint="Check your internet connection and Boomi platform status.",
            error_type="connection",
            details={"context": context} if context else None
        )

    # Generic error with context
    return format_error_response(
        error_message=f"Unexpected error: {error_str}",
        hint="Use invoke_boomi_api for advanced debugging or check Boomi platform status. If the issue persists, contact support.",
        error_type="unknown",
        details={
            "exception_type": exception_name,
            "context": context
        } if context else {"exception_type": exception_name}
    )


def format_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Format a standardized success response.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Standardized success response dict
    """
    response = {
        "success": True,
        "data": data
    }

    if message:
        response["message"] = message

    return response
