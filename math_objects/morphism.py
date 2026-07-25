"""
Morphism Module.

This module defines the PLTSMorphism class, which represents a morphism between PLTSs.
"""

from typing import Dict, List, Tuple, Any, Optional
from math_objects.model import Model
from math_objects.world import World
from ast import literal_eval


def _get_logger():
    from services.logging_service import get_logger
    return get_logger("PLTSMorphism")


class PLTSMorphism:
    """
    Represents a morphism between two PLTS models sharing the same underlying 
    twist structure, actions, and propositions.
    """

    def __init__(
        self,
        name: str,
        source_model: Model,
        target_model: Model,
        mapping: Dict[World, World],
        description: str = ""
    ):
        self.name = name
        self.source_model = source_model
        self.target_model = target_model
        self.mapping = mapping
        self.description = description or f"Morphism from {source_model.name_model} to {target_model.name_model}"

    def verify_morphism(self) -> Tuple[bool, List[str]]:
        """
        Verifies whether the mapping function satisfies the two morphism conditions.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        """
        errors = []
        ts = self.source_model.twist_structure
        
        if not ts or not hasattr(ts, 'truth_relation'):
            return False, ["Twist structure or truth relation is missing."]

        truth_leq = lambda a, b: (a, b) in ts.truth_relation
        bottom_pair = (ts.lattice.bottom, ts.lattice.top)

        for w in self.source_model.worlds:
            if w not in self.mapping or self.mapping[w] is None:
                errors.append(f"State '{w.name_short}' has no assigned target state in the mapping function.")

        if errors:
            return False, errors

        for w in self.source_model.worlds:
            hw = self.mapping.get(w)
            if not hw:
                continue
            for p in self.source_model.props:
                v_w = w.assignments.get(p, bottom_pair)
                v_hw = hw.assignments.get(p, bottom_pair)
                
                if isinstance(v_w, str):
                    try: v_w = literal_eval(v_w)
                    except: pass
                if isinstance(v_hw, str):
                    try: v_hw = literal_eval(v_hw)
                    except: pass

                norm_v_w = tuple(v_w) if isinstance(v_w, (list, tuple)) else v_w
                norm_v_hw = tuple(v_hw) if isinstance(v_hw, (list, tuple)) else v_hw
                
                if not truth_leq(norm_v_w, norm_v_hw):
                    errors.append(
                        f"Valuation condition failed for state '{w.name_short}' -> '{hw.name_short}' "
                        f"on proposition '{p}'."
                    )

        for act in self.source_model.actions:
            src_map = self.source_model.accessibility_relations.get(act, {})
            target_map = self.target_model.accessibility_relations.get(act, {})
            
            for w1, targets in src_map.items():
                hw1 = self.mapping.get(w1)
                hw1_targets = target_map.get(hw1, {}) if hw1 else {}
                
                for w2, weight in targets.items():
                    if weight == bottom_pair or weight is None:
                        continue
                        
                    hw2 = self.mapping.get(w2)
                    hw2_weight = hw1_targets.get(hw2, bottom_pair) if hw2 else bottom_pair
                    
                    norm_weight = tuple(weight) if isinstance(weight, (list, tuple)) else weight
                    norm_hw2_weight = tuple(hw2_weight) if isinstance(hw2_weight, (list, tuple)) else hw2_weight

                    if not truth_leq(norm_weight, norm_hw2_weight):
                        w1_name = w1.name_short if hasattr(w1, 'name_short') else str(w1)
                        w2_name = w2.name_short if hasattr(w2, 'name_short') else str(w2)
                        hw1_name = hw1.name_short if hw1 and hasattr(hw1, 'name_short') else str(hw1)
                        hw2_name = hw2.name_short if hw2 and hasattr(hw2, 'name_short') else str(hw2)
                        
                        errors.append(
                            f"Accessibility condition failed for action '{act}' on transition "
                            f"({w1_name} -> {w2_name}) mapped to ({hw1_name} -> {hw2_name})."
                        )

        return len(errors) == 0, errors