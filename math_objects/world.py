"""
World Module.

This module defines the World class, representing a single state in the model.
Each world is strictly associated with a specific Twist Structure.
"""

from typing import Dict, Optional, Any

def _get_logger():
    from services.logging_service import get_logger
    return get_logger("World")

class World:
    """
    Represents a single world in a Paraconsistent Modal Model.

    Attributes:
        name_long (str): Unique identifier.
        name_short (str): Display label.
        twist_structure (TwistStructure): The algebraic structure defining truth values.
        assignments (Dict[str, str]): Mapping of propositions to truth values (as strings).
    """

    def __init__(
        self, 
        name_long: str, 
        name_short: str, 
        twist_structure: Any, 
        assignments: Optional[Dict[str, str]] = None
    ):
        self.name_long = name_long
        self.name_short = name_short
        self.twist_structure = twist_structure
        self.assignments = assignments if assignments is not None else {}
        
        _get_logger().debug(f"World initialized: {self.name_short} ({self.name_long})")
    
    def get_assignment(self, variable: str) -> Optional[str]:
        val = self.assignments.get(variable)
        if val is None:
            _get_logger().debug(f"Assignment for '{variable}' not found in world '{self.name_short}'.")
        return val

    def assign_value(self, variable: str, value: str) -> None:
        """
        Assigns a value to a proposition.
        """
        try:
            self.assignments[variable] = value
            _get_logger().debug(f"Assignment updated: {self.name_short} | {variable} -> {value}")
        except Exception as e:
            _get_logger().error(f"Failed to assign value to {variable} in {self.name_short}: {e}")
            raise

    def __repr__(self) -> str:
        return f"{self.name_short}"