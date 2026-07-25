"""
JSON Handler Module.

Handles persistence of Lattices, Twist Structures, Worlds and Models.
"""

import json
import re
import os
from ast import literal_eval
from typing import Optional, List, Dict, Any
from config.config import PATHS
from services.logging_service import get_logger

from math_objects.lattice import Lattice, TwistStructure
from math_objects.world import World
from math_objects.model import Model
from math_objects.filters import LatticeFilter
from math_objects.filters import TwistFilter
from math_objects.model import FilteredModel
from math_objects.morphism import PLTSMorphism

logger = get_logger("JSONHandler")

class JSONHandler:

    @staticmethod
    def _load_safe(filename: str) -> Dict[str, Any]:
        """Safely loads JSON data from a file."""
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            return {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filename}: {str(e)}")
            return {}

    @staticmethod
    def _compact_json(data: Dict[str, Any]) -> str:
        """Formats JSON to keep lists and relation tuples on one line for readability."""
        json_str = json.dumps(data, indent=4)
        json_str = re.sub(r'\[\s+("[^"]+",?)\s+\]', r'[\1]', json_str)
        json_str = re.sub(r'\[\s+("[^"]+",)\s+("[^"]+")\s+\]', r'[\1 \2]', json_str)
        json_str = re.sub(r'\[\s+((?:\["[^"]+",\s*"[^"]+"\](?:,\s*)?)+)\s+\]', lambda m: f"[{m.group(1)}]", json_str)
        return json_str


    @staticmethod
    def load_config(filename: str) -> Dict[str, Any]:
        """Loads user configuration settings."""
        return JSONHandler._load_safe(filename)
    
    @staticmethod
    def save_config(filename: str, config: Dict[str, Any]) -> bool:
        """Saves user configuration settings."""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config to {filename}: {str(e)}")
            return False


    @staticmethod
    def load_lattice_from_json(filename: str, lattice_name: str) -> Optional[Lattice]:
        data = JSONHandler._load_safe(filename)
        if 'lattices' in data:
            for l_data in data['lattices']:
                if l_data.get('name') == lattice_name:
                    try:
                        elements = set(l_data.get('elements', []))
                        relations = set(tuple(r) for r in l_data.get('relations', []))
                        
                        raw_imp = l_data.get('implication_map', {})
                        implication_map = {}
                        for key_str, val in raw_imp.items():
                            try:
                                key_tuple = literal_eval(key_str)
                                implication_map[key_tuple] = val
                            except (ValueError, SyntaxError) as e:
                                logger.warning(f"Failed to parse implication map key '{key_str}' for lattice '{lattice_name}': {e}")
                                
                        return Lattice(lattice_name, elements, relations, implication_map)
                    except Exception as e:
                        logger.error(f"Error parsing lattice '{lattice_name}' in {filename}: {str(e)}")
        return None

    @staticmethod
    def save_lattice_to_json(filename: str, new_lattice: Lattice) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'lattices' not in data: 
                data['lattices'] = []
            
            l_list = [l for l in data['lattices'] if l.get('name') != new_lattice.name]
            
            imp_map_str = {str(k): v for k, v in new_lattice.implication_map.items()}
            
            l_dict = {
                "name": new_lattice.name,
                "elements": list(new_lattice.elements),
                "relations": [list(r) for r in new_lattice.relations],
                "implication_map": imp_map_str
            }
            l_list.append(l_dict)
            data['lattices'] = l_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving lattice '{new_lattice.name}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_lattice_from_json(filename: str, lattice_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'lattices' in data:
            data['lattices'] = [l for l in data['lattices'] if l.get('name') != lattice_name]
            with open(filename, 'w') as f: f.write(JSONHandler._compact_json(data))


    @staticmethod
    def load_twist_structure_from_json(filename: str, ts_name: str, lattices_file=PATHS["lattices"]) -> Optional[TwistStructure]:
        data = JSONHandler._load_safe(filename)
        if 'twist_structures' in data:
            for ts_data in data['twist_structures']:
                if ts_data.get('name') == ts_name:
                    lattice_name = ts_data.get('lattice_name')
                    lat = JSONHandler.load_lattice_from_json(lattices_file, lattice_name)
                    
                    if not lat:
                        logger.error(f"Failed to load base Lattice '{lattice_name}' for Twist Structure '{ts_name}'")
                        return None
                    
                    try:
                        ts = TwistStructure(lat)
                        ts.name = ts_name
                        if 'elements' in ts_data: 
                            ts.elements = {tuple(e) for e in ts_data['elements']}
                        if 'truth_relation' in ts_data: 
                            ts.truth_relation = {tuple(map(tuple, r)) for r in ts_data['truth_relation']}
                        if 'qntt_info_relation' in ts_data: 
                            ts.qntt_info_relation = {tuple(map(tuple, r)) for r in ts_data['qntt_info_relation']}
                        return ts
                    except Exception as e:
                        logger.error(f"Error parsing Twist Structure '{ts_name}': {str(e)}")
        return None

    @staticmethod
    def save_twist_structure_to_json(filename: str, new_ts: TwistStructure, name: str) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'twist_structures' not in data: 
                data['twist_structures'] = []
            
            l = [x for x in data['twist_structures'] if x.get('name') != name]
            
            elements_list = [list(e) for e in sorted(list(new_ts.elements))]
            truth_rel_list = [[list(a), list(b)] for a, b in sorted(list(new_ts.truth_relation))]
            info_rel_list = [[list(a), list(b)] for a, b in sorted(list(new_ts.qntt_info_relation))]

            l.append({
                "name": name, 
                "lattice_name": new_ts.lattice.name,
                "elements": elements_list,
                "truth_relation": truth_rel_list,
                "qntt_info_relation": info_rel_list
            })
            data['twist_structures'] = l
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Twist Structure '{name}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_twist_structure_from_json(filename: str, ts_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'twist_structures' in data:
            data['twist_structures'] = [x for x in data['twist_structures'] if x.get('name') != ts_name]
            with open(filename, 'w', encoding='utf-8') as f: f.write(JSONHandler._compact_json(data))

    @staticmethod
    def delete_twist_structure_from_json(filename: str, ts_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'twist_structures' in data:
            data['twist_structures'] = [x for x in data['twist_structures'] if x.get('name') != ts_name]
            with open(filename, 'w') as f: f.write(JSONHandler._compact_json(data))


    @staticmethod
    def load_world_from_json(filename: str, world_name: str, twist_file: str = PATHS["twist_structures"]) -> Optional[World]:
        data = JSONHandler._load_safe(filename)
        if 'worlds' in data:
            for w in data['worlds']:
                if w.get('world_name') == world_name:
                    try:
                        ts_name = w.get('twist_structure_name')
                        ts = None
                        if ts_name:
                            ts = JSONHandler.load_twist_structure_from_json(twist_file, ts_name)
                            if not ts:
                                logger.warning(f"Could not load Twist Structure '{ts_name}' for World '{world_name}'.")
                        
                        return World(
                            world_name, 
                            w.get('short_world_name'), 
                            ts, 
                            w.get('assignments', {})
                        )
                    except Exception as e:
                        logger.error(f"Error parsing World '{world_name}' from {filename}: {str(e)}")
        return None

    @staticmethod
    def save_world_to_json(filename: str, new_world: World) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'worlds' not in data: 
                data['worlds'] = []
            
            w_list = [w for w in data['worlds'] if w.get('world_name') != new_world.name_long]
            
            w_dict = {
                "world_name": new_world.name_long,
                "short_world_name": new_world.name_short,
                "twist_structure_name": new_world.twist_structure.name if new_world.twist_structure else None,
                "assignments": new_world.assignments
            }
            w_list.append(w_dict)
            data['worlds'] = w_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e: 
            logger.error(f"Error saving world '{new_world.name_long}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_world_from_json(filename: str, w_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'worlds' in data:
            data['worlds'] = [w for w in data['worlds'] if w.get('world_name') != w_name]
            with open(filename, 'w') as f: f.write(JSONHandler._compact_json(data))


    @staticmethod
    def load_model_from_json(
        filename: str, 
        model_name: str, 
        worlds_file: str = PATHS["worlds"],
        twist_file: str = PATHS["twist_structures"]
    ) -> Optional[Model]:
        data = JSONHandler._load_safe(filename)
        if 'models' in data:
            for m in data['models']:
                if m.get('model_name') == model_name:
                    try:
                        ts_name = m.get('twist_structure_name')
                        ts = JSONHandler.load_twist_structure_from_json(twist_file, ts_name)
                        if not ts:
                            logger.error(f"Failed to load required Twist Structure '{ts_name}' for model '{model_name}'")
                            return None
                        
                        w_set, w_map = set(), {}
                        for wn in m.get("worlds", []):
                            w_obj = JSONHandler.load_world_from_json(worlds_file, wn)
                            if w_obj:
                                w_set.add(w_obj)
                                w_map[w_obj.name_long] = w_obj
                            else:
                                logger.warning(f"Could not load world '{wn}' for model '{model_name}'")
                        
                        rels = {}
                        raw_rels = m.get("accessibility_relations", {})
                        
                        for act, src_map in raw_rels.items():
                            rels[act] = {}
                            for src_name, tgt_data in src_map.items():
                                if src_name in w_map:
                                    src_w = w_map[src_name]
                                    rels[act][src_w] = {}
                                    
                                    if isinstance(tgt_data, dict):
                                        for tgt_name, weight in tgt_data.items():
                                            if tgt_name in w_map:
                                                rels[act][src_w][w_map[tgt_name]] = tuple(weight)
                                    
                                    elif isinstance(tgt_data, list):
                                        top_val = (ts.residuated_lattice.top, ts.residuated_lattice.bottom)
                                        for tgt_name in tgt_data:
                                            if tgt_name in w_map:
                                                rels[act][src_w][w_map[tgt_name]] = top_val

                        return Model(
                            model_name, ts, w_set,
                            rels, set(m.get('props', [])), set(raw_rels.keys()), 
                            description=m.get('description', "")
                        )
                    except Exception as e: 
                        logger.error(f"Error loading model '{model_name}' from {filename}: {str(e)}")
                        return None
        return None

    @staticmethod
    def save_model_to_json(filename: str, new_model: Model) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'models' not in data: 
                data['models'] = []
            
            m_list = [m for m in data['models'] if m.get('model_name') != new_model.name_model]
            
            acc_json = {}
            for act in new_model.actions:
                acc_json[act] = {}
                if act in new_model.accessibility_relations:
                    for src, target_map in new_model.accessibility_relations[act].items():
                        t_json = {}
                        for tgt, weight in target_map.items():
                            t_json[tgt.name_long] = list(weight)
                        
                        if t_json:
                            acc_json[act][src.name_long] = t_json

            m_list.append({
                "model_name": new_model.name_model,
                "description": new_model.description,
                "twist_structure_name": new_model.twist_structure.name,
                "worlds": [w.name_long for w in new_model.worlds],
                "accessibility_relations": acc_json,
                "props": list(new_model.props)
            })
            data['models'] = m_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Model '{new_model.name_model}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_model_from_json(filename: str, model_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'models' in data:
            data['models'] = [m for m in data['models'] if m.get('model_name') != model_name]
            with open(filename, 'w') as f: f.write(JSONHandler._compact_json(data))

    @staticmethod
    def get_names_from_json(filename: str, json_key: str, name_key: str) -> List[str]:
        data = JSONHandler._load_safe(filename)
        return [i[name_key] for i in data.get(json_key, []) if name_key in i]


    @staticmethod
    def load_lattice_filter_from_json(filename: str, filter_name: str, lattices_file=PATHS["lattices"]) -> Optional[Any]:
        data = JSONHandler._load_safe(filename)
        if 'lattice_filters' in data:
            for lf_data in data['lattice_filters']:
                if lf_data.get('name') == filter_name:
                    try:
                        lattice_name = lf_data.get('lattice_name')
                        base_lattice = JSONHandler.load_lattice_from_json(lattices_file, lattice_name)
                        if not base_lattice:
                            logger.error(f"Failed to load base Lattice '{lattice_name}' for Lattice Filter '{filter_name}'")
                            return None
                        
                        filter_elements = set(lf_data.get('filter_elements', []))
                        return LatticeFilter(filter_name, lattice_name, filter_elements, base_lattice)
                    except Exception as e:
                        logger.error(f"Error parsing Lattice Filter '{filter_name}': {str(e)}")
        return None

    @staticmethod
    def save_lattice_filter_to_json(filename: str, new_filter: Any) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'lattice_filters' not in data: 
                data['lattice_filters'] = []
            
            f_list = [f for f in data['lattice_filters'] if f.get('name') != new_filter.name]
            
            f_dict = {
                "name": new_filter.name,
                "lattice_name": new_filter.lattice_name,
                "filter_elements": list(new_filter.filter_elements)
            }
            f_list.append(f_dict)
            data['lattice_filters'] = f_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Lattice Filter '{new_filter.name}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_lattice_filter_from_json(filename: str, filter_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'lattice_filters' in data:
            data['lattice_filters'] = [f for f in data['lattice_filters'] if f.get('name') != filter_name]
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))


    @staticmethod
    def load_twist_filter_from_json(filename: str, filter_name: str, twist_file=PATHS["twist_structures"], lattice_filters_file=PATHS["lattice_filters"]) -> Optional[Any]:
        data = JSONHandler._load_safe(filename)
        if 'twist_filters' in data:
            for tf_data in data['twist_filters']:
                if tf_data.get('name') == filter_name:
                    try:
                        twist_name = tf_data.get('twist_name')
                        lattice_filter_name = tf_data.get('lattice_filter_name')
                        
                        twist_struct = JSONHandler.load_twist_structure_from_json(twist_file, twist_name)
                        if not twist_struct:
                            logger.error(f"Failed to load Twist Structure '{twist_name}' for Twist Filter '{filter_name}'")
                            return None
                        
                        lattice_filter = JSONHandler.load_lattice_filter_from_json(lattice_filters_file, lattice_filter_name)
                        if not lattice_filter:
                            logger.error(f"Failed to load underlying Lattice Filter '{lattice_filter_name}' for Twist Filter '{filter_name}'")
                            return None
                        
                        return TwistFilter(filter_name, twist_name, lattice_filter, twist_struct)
                    except Exception as e:
                        logger.error(f"Error parsing Twist Filter '{filter_name}': {str(e)}")
        return None

    @staticmethod
    def save_twist_filter_to_json(filename: str, new_twist_filter: Any) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'twist_filters' not in data: 
                data['twist_filters'] = []
            
            tf_list = [tf for tf in data['twist_filters'] if tf.get('name') != new_twist_filter.name]
            
            tf_dict = {
                "name": new_twist_filter.name,
                "twist_name": new_twist_filter.twist_name,
                "lattice_filter_name": new_twist_filter.lattice_filter.name,
                "filter_elements": [list(e) for e in sorted(list(new_twist_filter.filter_elements))]
            }
            tf_list.append(tf_dict)
            data['twist_filters'] = tf_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Twist Filter '{new_twist_filter.name}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_twist_filter_from_json(filename: str, filter_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'twist_filters' in data:
            data['twist_filters'] = [tf for tf in data['twist_filters'] if tf.get('name') != filter_name]
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))

    @staticmethod
    def load_filtered_model_from_json(
        filename: str, 
        filtered_model_name: str, 
        models_file: str = PATHS["models"],
        twist_filters_file: str = PATHS["twist_filters"]
    ) -> Optional[FilteredModel]:
        data = JSONHandler._load_safe(filename)
        if 'filtered_models' in data:
            for fm in data['filtered_models']:
                if fm.get('filtered_model_name') == filtered_model_name:
                    try:
                        base_model_name = fm.get('base_model_name')
                        twist_filter_name = fm.get('twist_filter_name')
                        
                        base_model = JSONHandler.load_model_from_json(models_file, base_model_name)
                        if not base_model:
                            logger.error(f"Failed to load base model '{base_model_name}' for filtered model '{filtered_model_name}'")
                            return None
                        
                        twist_filter = JSONHandler.load_twist_filter_from_json(twist_filters_file, twist_filter_name)
                        if not twist_filter:
                            logger.error(f"Failed to load twist filter '{twist_filter_name}' for filtered model '{filtered_model_name}'")
                            return None
                        
                        return FilteredModel(base_model, twist_filter, name_model=filtered_model_name)
                    except Exception as e:
                        logger.error(f"Error loading filtered model '{filtered_model_name}' from {filename}: {str(e)}")
                        return None
        return None

    @staticmethod
    def save_filtered_model_to_json(filename: str, filtered_model: FilteredModel) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'filtered_models' not in data: 
                data['filtered_models'] = []
            
            fm_list = [fm for fm in data['filtered_models'] if fm.get('filtered_model_name') != filtered_model.name_model]
            
            fm_list.append({
                "filtered_model_name": filtered_model.name_model,
                "base_model_name": filtered_model.base_model.name_model,
                "twist_filter_name": filtered_model.twist_filter.name,
                "description": filtered_model.description
            })
            data['filtered_models'] = fm_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Filtered Model '{filtered_model.name_model}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_filtered_model_from_json(filename: str, filtered_model_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'filtered_models' in data:
            data['filtered_models'] = [fm for fm in data['filtered_models'] if fm.get('filtered_model_name') != filtered_model_name]
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))

    @staticmethod
    def load_morphism_from_json(
        filename: str, 
        morphism_name: str, 
        models_file: str = PATHS["models"]
    ) -> Optional[PLTSMorphism]:
        data = JSONHandler._load_safe(filename)
        if 'morphisms' in data:
            for m_data in data['morphisms']:
                if m_data.get('name') == morphism_name:
                    try:
                        source_name = m_data.get('source_model')
                        target_name = m_data.get('target_model')
                        mapping_raw = m_data.get('mapping', {})
                        
                        source_model = JSONHandler.load_model_from_json(models_file, source_name)
                        target_model = JSONHandler.load_model_from_json(models_file, target_name)
                        
                        if not source_model or not target_model:
                            logger.error(f"Failed to load source or target model for morphism '{morphism_name}'")
                            return None
                        
                        mapping = {}
                        src_world_map = {w.name_long: w for w in source_model.worlds}
                        tgt_world_map = {w.name_long: w for w in target_model.worlds}
                        
                        for src_w_name, tgt_w_name in mapping_raw.items():
                            if src_w_name in src_world_map and tgt_w_name in tgt_world_map:
                                mapping[src_world_map[src_w_name]] = tgt_world_map[tgt_w_name]
                        
                        return PLTSMorphism(
                            name=morphism_name,
                            source_model=source_model,
                            target_model=target_model,
                            mapping=mapping,
                            description=m_data.get('description', "")
                        )
                    except Exception as e:
                        logger.error(f"Error loading morphism '{morphism_name}' from {filename}: {str(e)}")
                        return None
        return None

    @staticmethod
    def save_morphism_to_json(filename: str, morphism: PLTSMorphism) -> bool:
        try:
            data = JSONHandler._load_safe(filename)
            if 'morphisms' not in data: 
                data['morphisms'] = []
            
            m_list = [m for m in data['morphisms'] if m.get('name') != morphism.name]
            
            mapping_dict = {src_w.name_long: tgt_w.name_long for src_w, tgt_w in morphism.mapping.items()}
            
            m_list.append({
                "name": morphism.name,
                "source_model": morphism.source_model.name_model,
                "target_model": morphism.target_model.name_model,
                "mapping": mapping_dict,
                "description": morphism.description
            })
            data['morphisms'] = m_list
            
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))
            return True
        except Exception as e:
            logger.error(f"Error saving Morphism '{morphism.name}' to {filename}: {str(e)}")
            return False

    @staticmethod
    def delete_morphism_from_json(filename: str, morphism_name: str) -> None:
        data = JSONHandler._load_safe(filename)
        if 'morphisms' in data:
            data['morphisms'] = [m for m in data['morphisms'] if m.get('name') != morphism_name]
            with open(filename, 'w', encoding='utf-8') as f: 
                f.write(JSONHandler._compact_json(data))