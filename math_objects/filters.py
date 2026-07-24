from typing import Set, Tuple
from math_objects.lattice import Lattice, TwistStructure

class LatticeFilter:
    """Represents a filter subset defined on a specific base Lattice."""
    def __init__(self, name: str, lattice_name: str, filter_elements: Set[str], lattice: Lattice):
        self.name = name
        self.lattice_name = lattice_name
        self.filter_elements = set(filter_elements)
        self.lattice = lattice

        if not self._is_valid_filter():
            raise ValueError(f"Filter '{name}' is not a valid filter for lattice '{lattice_name}'.")

    def _is_valid_filter(self) -> bool:
        try:
            if (not self.filter_elements) or (self.filter_elements == self.lattice.elements):
                return False
            
            for x in self.filter_elements:
                for y in self.filter_elements:
                    if self.lattice.meet(x, y) not in self.filter_elements:
                        return False
                    if self.lattice.join(x,y) not in self.filter_elements:
                        return False
            
            for x in self.lattice.elements:
                for y in self.lattice.elements:
                    if self.lattice.meet(x, y) in self.filter_elements:
                        if x not in self.filter_elements or y not in self.filter_elements:
                            return False
                    if self.lattice.join(x, y) in self.filter_elements:
                        if x not in self.filter_elements and y not in self.filter_elements:
                            return False
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"LatticeFilter({self.name} on {self.lattice_name})"


class TwistFilter:
    """Automatically generates and stores a twist filter based on an underlying LatticeFilter."""
    def __init__(self, name: str, twist_name: str, lattice_filter: LatticeFilter, twist_structure: TwistStructure):
        self.name = name
        self.twist_name = twist_name
        self.lattice_filter = lattice_filter
        self.twist_structure = twist_structure
        self.filter_elements = self._build_twist_filter()

    def _build_twist_filter(self) -> Set[Tuple[str, str]]:
        fil = set()
        for x in self.lattice_filter.filter_elements:
            for y in self.twist_structure.lattice.elements:
                fil.add((x, y))
        return fil

    def __repr__(self) -> str:
        return f"TwistFilter({self.name} for {self.twist_name})"