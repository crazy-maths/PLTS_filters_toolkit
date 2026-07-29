"""
Morphism Module.

This module defines the PLTSMorphism class, which represents a morphism between PLTSs.
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
from math_objects.model import Model
from math_objects.world import World
from ast import literal_eval

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

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
    
    def draw_graph(self) -> None:

        if not VISUALIZATION_AVAILABLE:
            _get_logger().warning("Visualization libraries not installed. Cannot draw graph.")
            return

        plt.figure(figsize=(14, 8))
        plt.title(f"Morphism Visualization: {self.name}\n({self.source_model.name_model} ──> {self.target_model.name_model})", fontsize=14, fontweight="bold")

        Gs = nx.DiGraph()
        for w in self.source_model.worlds:
            Gs.add_node(w.name_short)
            
        Gt = nx.DiGraph()
        for w in self.target_model.worlds:
            Gt.add_node(w.name_short)

        pos_s_raw = nx.spring_layout(Gs, k=2.0, seed=42)
        pos_t_raw = nx.spring_layout(Gt, k=2.0, seed=42)

        pos = {}
        for node, (x, y) in pos_s_raw.items():
            pos[f"src_{node}"] = (x - 3.0, y)
        for node, (x, y) in pos_t_raw.items():
            pos[f"tgt_{node}"] = (x + 3.0, y)

        G_master = nx.DiGraph()
        for w in self.source_model.worlds:
            G_master.add_node(f"src_{w.name_short}", color="darkblue", label=w.name_short)
        for w in self.target_model.worlds:
            G_master.add_node(f"tgt_{w.name_short}", color="darkorange", label=w.name_short)

        NODE_SIZE = 2500

        src_edge_data = defaultdict(list)
        lat_s = self.source_model.twist_structure.lattice
        bottom_s = (lat_s.bottom, lat_s.top)
        
        for act, matrix in self.source_model.accessibility_relations.items():
            for src, targets in matrix.items():
                for tgt, weight in targets.items():
                    if weight is None or weight == bottom_s:
                        continue
                    u, v = f"src_{src.name_short}", f"src_{tgt.name_short}"
                    w_str = str(weight).replace("'", "").replace('"', "").replace(" ", "")
                    src_edge_data[(u, v)].append(f"{act}: {w_str}")

        for (u, v), text_list in src_edge_data.items():
            full_text = "\n".join(text_list)
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            if u == v:
                x, y = x1, y1
                dx, dy = 0.25, 0.22
                verts = [(x, y), (x + dx, y + dy), (x - dx, y + dy), (x, y)]
                path = Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
                plt.gca().add_patch(PathPatch(path, edgecolor="darkblue", linewidth=1.2, facecolor="none", zorder=1.5))
                plt.text(x, y + dy * 0.55, full_text, ha="center", va="center", fontsize=7, color="darkblue",
                        bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9, boxstyle="round,pad=0.15"))
            else:
                nx.draw_networkx_edges(G_master, pos, edgelist=[(u, v)], arrowstyle="-|>", arrowsize=20, edge_color="darkblue", width=1.5, node_size=NODE_SIZE)
                plt.text((x1 + x2) / 2, (y1 + y2) / 2, full_text, ha='center', va='center', fontsize=7, color='darkblue',
                        bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, boxstyle='round,pad=0.2'))

        tgt_edge_data = defaultdict(list)
        lat_t = self.target_model.twist_structure.lattice
        bottom_t = (lat_t.bottom, lat_t.top)

        for act, matrix in self.target_model.accessibility_relations.items():
            for src, targets in matrix.items():
                for tgt, weight in targets.items():
                    if weight is None or weight == bottom_t:
                        continue
                    u, v = f"tgt_{src.name_short}", f"tgt_{tgt.name_short}"
                    w_str = str(weight).replace("'", "").replace('"', "").replace(" ", "")
                    tgt_edge_data[(u, v)].append(f"{act}: {w_str}")

        for (u, v), text_list in tgt_edge_data.items():
            full_text = "\n".join(text_list)
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            if u == v:
                x, y = x1, y1
                dx, dy = 0.25, 0.22
                verts = [(x, y), (x + dx, y + dy), (x - dx, y + dy), (x, y)]
                path = Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
                plt.gca().add_patch(PathPatch(path, edgecolor="darkorange", linewidth=1.2, facecolor="none", zorder=1.5))
                plt.text(x, y + dy * 0.55, full_text, ha="center", va="center", fontsize=7, color="darkorange",
                        bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9, boxstyle="round,pad=0.15"))
            else:
                nx.draw_networkx_edges(G_master, pos, edgelist=[(u, v)], arrowstyle="-|>", arrowsize=20, edge_color="darkorange", width=1.5, node_size=NODE_SIZE)
                plt.text((x1 + x2) / 2, (y1 + y2) / 2, full_text, ha='center', va='center', fontsize=7, color='darkorange',
                        bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, boxstyle='round,pad=0.2'))

        mapping_edges = []
        for sw, tw in self.mapping.items():
            if tw:
                mapping_edges.append((f"src_{sw.name_short}", f"tgt_{tw.name_short}"))

        nx.draw_networkx_edges(G_master, pos, edgelist=mapping_edges, edge_color="gray", style="dotted", width=2.0, arrowstyle="-|>", arrowsize=18, node_size=NODE_SIZE)

        src_nodes = [n for n, d in G_master.nodes(data=True) if n.startswith("src_")]
        tgt_nodes = [n for n, d in G_master.nodes(data=True) if n.startswith("tgt_")]
        
        nx.draw_networkx_nodes(G_master, pos, nodelist=src_nodes, node_size=NODE_SIZE, node_color="#99ccff", edgecolors="darkblue", linewidths=2.0)
        nx.draw_networkx_nodes(G_master, pos, nodelist=tgt_nodes, node_size=NODE_SIZE, node_color="#ffcc99", edgecolors="darkorange", linewidths=2.0)
        
        node_labels = {n: d["label"] for n, d in G_master.nodes(data=True)}
        nx.draw_networkx_labels(G_master, pos, labels=node_labels, font_size=9, font_weight="bold")

        max_y = max(y for _, y in pos.values())
        header_y = max_y + 0.8

        plt.text(-3.0, header_y, f"Source: {self.source_model.name_model}", ha="center", fontsize=11, fontweight="bold", color="darkblue")
        plt.text(3.0, header_y, f"Target: {self.target_model.name_model}", ha="center", fontsize=11, fontweight="bold", color="darkorange")

        plt.axis("off")
        plt.tight_layout()
        plt.show()