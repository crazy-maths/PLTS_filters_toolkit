from math_objects.lattice import Lattice, TwistStructure
from math_objects.world import World
from math_objects.model import Model, FilteredModel
from services.json_handler import JSONHandler
from services.logging_service import get_logger
from typing import Dict, Any
from math_objects.filters import LatticeFilter, TwistFilter
from config import PATHS

logger = get_logger("ObjectManager")

class ObjectManager:
    def __init__(self):
        self.lattices: Dict[str, Lattice] = {}
        self.twist_structures: Dict[str, TwistStructure] = {}
        self.worlds: Dict[str, World] = {}
        self.models: Dict[str, Model] = {}
        self.filtered_models: Dict[str, FilteredModel] = {}
        self.lattice_filters: Dict[str, LatticeFilter] = {}
        self.twist_filters: Dict[str, TwistFilter] = {}

    def register_object(self, name: str, obj: Any, type_str: str):
        mapping = {
            "Lattice": self.lattices,
            "Lattice Filter": self.lattice_filters,
            "Twist Structure": self.twist_structures,
            "Twist Filter": self.twist_filters,
            "World": self.worlds,
            "Model": self.models,
            "Filtered Model": self.filtered_models
        }
        if type_str in mapping:
            mapping[type_str][name] = obj
            logger.info(f"Registered {type_str}: {name}")
        else:
            logger.warning(f"Attempted to register unknown type: {type_str}")

    def is_object_loaded(self, category: str, name: str) -> bool:
        mapping = {
            "Lattice": self.lattices,
            "Lattice Filter": self.lattice_filters,
            "Twist Structure": self.twist_structures,
            "Twist Filter": self.twist_filters,
            "World": self.worlds,
            "Model": self.models,
            "Filtered Model": self.filtered_models
        }
        return name in mapping.get(category, {})

    def get_object(self, category: str, name: str):
        mapping = {
            "Lattice": self.lattices,
            "Lattice Filter": self.lattice_filters,
            "Twist Structure": self.twist_structures,
            "Twist Filter": self.twist_filters,
            "World": self.worlds,
            "Model": self.models,
            "Filtered Model": self.filtered_models
        }
        obj = mapping.get(category, {}).get(name)
        if not obj:
            logger.debug(f"Object '{name}' not found in category '{category}'")
        return obj

    def delete_object(self, ui_category: str, name: str):
        mapping = {
            "Lattice": self.lattices,
            "Lattice Filter": self.lattice_filters,
            "Twist Structure": self.twist_structures,
            "Twist Filter": self.twist_filters,
            "World": self.worlds,
            "Model": self.models,
            "Filtered Model": self.filtered_models
        }
        
        target_dict = mapping.get(ui_category)
        if target_dict is not None:
            if name in target_dict:
                del target_dict[name]
                logger.info(f"Deleted {ui_category}: {name}")
                return
            else:
                logger.debug(f"Object '{name}' was already absent from memory dictionary for '{ui_category}'.")
                return

        logger.warning(f"Attempted to delete non-existent object: {ui_category} - {name}")

    def create_lattice_filter(self, filter_name: str, lattice_name: str, filter_elements: set) -> bool:
        if lattice_name not in self.lattices:
            raise ValueError(f"Lattice '{lattice_name}' not loaded.")
        
        lattice = self.lattices[lattice_name]
        
        if lattice.bottom in filter_elements:
            raise ValueError("The bottom element of the lattice cannot be part of a filter.")
            
        from math_objects.filters import LatticeFilter, TwistFilter
        
        lat_filter = LatticeFilter(filter_name, lattice_name, filter_elements, lattice)
        if JSONHandler.save_lattice_filter_to_json(PATHS["lattice_filters"], lat_filter):
            self.lattice_filters[filter_name] = lat_filter
            
            all_twist_names = set(self.twist_structures.keys())
            file_twist_names = JSONHandler.get_names_from_json(PATHS["twist_structures"], "twist_structures", "name")
            
            for ts_name in set(list(all_twist_names) + list(file_twist_names)):
                ts_obj = self.twist_structures.get(ts_name) or JSONHandler.load_twist_structure_from_json(PATHS["twist_structures"], ts_name)
                
                if ts_obj:
                    lat_ref = getattr(ts_obj, 'lattice', None)
                    if lat_ref and lat_ref.name == lattice_name:
                        tf_name = f"{filter_name}_twist_{ts_name}"
                        t_filter = TwistFilter(tf_name, ts_name, lat_filter, ts_obj)
                        if JSONHandler.save_twist_filter_to_json(PATHS["twist_filters"], t_filter):
                            self.twist_filters[tf_name] = t_filter
                        else:
                            logger.error(f"Failed to save Twist Filter '{tf_name}' to JSON.")
            return True
        return False

    def auto_create_top_filter(self, lattice: Lattice):
        """Automatically creates the trivial filter containing only the top element."""
        top_filter_name = f"TopFilter_{lattice.name}"
        top_element_set = {lattice.top}
        
        if top_filter_name not in self.lattice_filters:
            try:
                self.create_lattice_filter(top_filter_name, lattice.name, top_element_set)
            except Exception as e:
                pass