"""
Pydantic models for Boomi MCP Server.

These models provide type safety and validation for all MCP tool operations.
"""

from .process_models import (
    ShapeConfig,
    ProcessConfig,
    ComponentSpec,
)

__all__ = [
    'ShapeConfig',
    'ProcessConfig',
    'ComponentSpec',
]
