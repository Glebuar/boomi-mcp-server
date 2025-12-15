"""
Boomi Process XML Builders.

Builder classes that use templates to construct process XML.
Handles logic like coordinate calculation, validation, and connection management.
"""

from .coordinate_calculator import CoordinateCalculator
from .process_builder import ProcessBuilder

__all__ = [
    "CoordinateCalculator",
    "ProcessBuilder",
]
