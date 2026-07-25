"""
Model Module.

This module defines the Model class, which represents a paraconsistent model
extended to support Multi-Modal Logic over a specific Twist Structure.
"""

from typing import Set, Dict, Optional, Any, Tuple
from collections import defaultdict
from math_objects.world import World
import math


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
    return get_logger("Model")


class Model:
    """
    Represents a Paraconsistent Model (W, R, V).
    """

    def __init__(
        self,
        name_model: str,
        twist_structure: Any,
        worlds: Set[World],
        accessibility_relations: Optional[Dict[str, Dict[World, Dict[World, Tuple[str, str]]]]] = None,
        props: Optional[Set[str]] = None,
        actions: Optional[Set[str]] = None,
        description: str = None
    ):
        for world in worlds:
            if not isinstance(world, World):
                raise TypeError("The 'worlds' argument must contain instances of World.")

        self.name_model = name_model
        self.twist_structure = twist_structure
        self.worlds = worlds
        self.props = props if props is not None else set()
        self.actions = actions if actions is not None else set()
        self.description = description
        self.accessibility_relations = defaultdict(lambda: defaultdict(dict))

        if accessibility_relations:
            self.actions.update(accessibility_relations.keys())
            for action, src_map in accessibility_relations.items():
                for src, target_map in src_map.items():
                    for tgt, weight in target_map.items():
                        if weight is not None:
                            self.accessibility_relations[action][src][tgt] = weight

    def get_relation_weight(self, action: str, source: World, target: World) -> Tuple[str, str]:
        try:
            if action in self.accessibility_relations:
                if source in self.accessibility_relations[action]:
                    if target in self.accessibility_relations[action][source]:
                        return self.accessibility_relations[action][source][target]

            lat = self.twist_structure.lattice
            return (lat.bottom, lat.top)
        except Exception as e:
            _get_logger().error(f"Error retrieving weight for {action} from {source.name_short} to {target.name_short}: {e}")
            raise

    def get_world(self, name_short: str) -> Optional[World]:
        for world in self.worlds:
            if world.name_short == name_short:
                return world
        return None

    def draw_graph(self, action: Optional[str] = None) -> None:
        if not VISUALIZATION_AVAILABLE:
            _get_logger().warning("Visualization libraries not installed. Cannot draw graph.")
            return

        G = nx.DiGraph()
        for world in self.worlds:
            G.add_node(world.name_short)

        if action:
            if action not in self.actions:
                _get_logger().error(f"Action '{action}' requested but not found in model.")
                return
            actions_to_draw = [action]
            title = f"PLTS: {self.name_model} (Action: {action})"
        else:
            actions_to_draw = sorted(list(self.actions))
            title = f"PLTS: {self.name_model}"

        try:
            edge_data = defaultdict(list)

            lat = self.twist_structure.lattice
            bottom_pair = (
                lat.bottom,
                lat.top
            )

            for act in actions_to_draw:
                if act in self.accessibility_relations:
                    for src, targets in self.accessibility_relations[act].items():
                        for tgt, weight in targets.items():
                            if weight is None or weight == bottom_pair:
                                continue
                            u, v = src.name_short, tgt.name_short
                            w_str = str(weight).replace("'", "").replace('"', "").replace(" ", "")
                            label_str = f"{act}: {w_str}"
                            edge_data[(u, v)].append(label_str)

            plt.figure(figsize=(12, 10))
            pos = nx.spring_layout(G, k=3.0, seed=42) 
            
            NODE_SIZE = 2500
            
            node_colors = "#99ccff"
            nx.draw_networkx_nodes(G, pos, node_size=NODE_SIZE, node_color=node_colors, edgecolors="black", linewidths=1.5)
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

            for (u, v), text_list in edge_data.items():
                full_text = "\n".join(text_list)
                
                is_bidirectional = (v, u) in edge_data and u != v
                is_self_loop = (u == v)

                if is_self_loop:
                    x, y = pos[u]

                    loop_size = 0.30
                    dx = loop_size
                    dy = loop_size * 0.9

                    verts = [
                        (x, y),              
                        (x + dx, y + dy),     
                        (x - dx, y + dy),     
                        (x, y),            
                    ]
                    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]

                    path = Path(verts, codes)
                    patch = PathPatch(
                        path,
                        edgecolor="#555555",
                        linewidth=1.4,
                        facecolor="none",
                        zorder=1.5,
                    )
                    plt.gca().add_patch(patch)

                    label_y_offset = dy * 0.55
                    plt.text(
                        x,
                        y + label_y_offset,
                        full_text,
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="darkblue",
                        zorder=3,
                        bbox=dict(
                            facecolor="white",
                            edgecolor="lightgray",
                            alpha=0.9,
                            pad=0.25,
                            boxstyle="round,pad=0.15",
                        ),
                    )

                    continue


                x1, y1 = pos[u]
                x2, y2 = pos[v]
                
                if is_bidirectional:
                    rad = 0.2
                    nx.draw_networkx_edges(
                        G, pos, edgelist=[(u,v)], 
                        connectionstyle=f"arc3,rad={rad}", 
                        arrowstyle="-|>", arrowsize=25, edge_color="#555555", width=1.5,
                        node_size=NODE_SIZE
                    )
                    
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    vx, vy = x2 - x1, y2 - y1
                    dist = math.sqrt(vx**2 + vy**2)
                    if dist == 0: dist = 1 
                    
                    nx_vec, ny_vec = vy/dist, -vx/dist
                    offset = rad * dist * 0.6 
                    lx = mx + nx_vec * offset
                    ly = my + ny_vec * offset
                    
                    plt.text(lx, ly, full_text, horizontalalignment='center', verticalalignment='center', fontsize=8, color='darkblue', 
                            bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, pad=0.3, boxstyle='round,pad=0.2'))

                else:
                    nx.draw_networkx_edges(
                        G, pos, edgelist=[(u,v)], 
                        arrowstyle="-|>", arrowsize=25, edge_color="#555555", width=1.5,
                        node_size=NODE_SIZE
                    )
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    plt.text(mx, my, full_text, horizontalalignment='center', verticalalignment='center', fontsize=8, color='darkblue', 
                            bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, pad=0.3, boxstyle='round,pad=0.2'))

            plt.title(title, fontsize=14, fontweight='bold')
            plt.axis("off")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            _get_logger().error(f"Failed to draw model graph: {e}")


class FilteredModel:
    """
    Represents an independent Filtered Paraconsistent Model derived from a base Model 
    and a TwistFilter. The states W remain the same, but the accessibility 
    relations are unweighted and crisp based on the twist filter.
    """

    def __init__(self, base_model: Model, twist_filter: Any, name_model: Optional[str] = None):
        self.name_model = name_model or f"{base_model.name_model}_filtered_{twist_filter.name}"
        self.base_model = base_model
        self.twist_filter = twist_filter
        self.twist_structure = base_model.twist_structure
        self.worlds = base_model.worlds
        self.props = base_model.props
        self.actions = base_model.actions
        self.description = f"Filtered model derived from {base_model.name_model} using twist filter {twist_filter.name}"

        self.accessibility_relations = defaultdict(lambda: defaultdict(dict))
        filter_elements = twist_filter.filter_elements

        for action, src_map in base_model.accessibility_relations.items():
            for src, target_map in src_map.items():
                for tgt, weight in target_map.items():
                    if weight in filter_elements:
                        self.accessibility_relations[action][src][tgt] = True

    def get_world(self, name_short: str) -> Optional[World]:
        for world in self.worlds:
            if world.name_short == name_short:
                return world
        return None

    def draw_graph(self, action: Optional[str] = None) -> None:
        """Draws the filtered unweighted graph."""
        if not VISUALIZATION_AVAILABLE:
            _get_logger().warning("Visualization libraries not installed. Cannot draw graph.")
            return

        G = nx.DiGraph()
        for world in self.worlds:
            G.add_node(world.name_short)

        if action:
            if action not in self.actions:
                _get_logger().error(f"Action '{action}' requested but not found in filtered model.")
                return
            actions_to_draw = [action]
            title = f"Filtered Model: {self.name_model} (Action: {action})"
        else:
            actions_to_draw = sorted(list(self.actions))
            title = f"Filtered Model: {self.name_model}"

        try:
            edge_data = defaultdict(list)
            for act in actions_to_draw:
                if act in self.accessibility_relations:
                    for src, targets in self.accessibility_relations[act].items():
                        for tgt in targets.keys():
                            u, v = src.name_short, tgt.name_short
                            edge_data[(u, v)].append(act)

            plt.figure(figsize=(12, 10))
            pos = nx.spring_layout(G, k=3.0, seed=42)
            
            NODE_SIZE = 2500
            nx.draw_networkx_nodes(G, pos, node_size=NODE_SIZE, node_color="#99ccff", edgecolors="black", linewidths=1.5)
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

            for (u, v), act_list in edge_data.items():
                full_text = ", ".join(act_list)
                is_bidirectional = (v, u) in edge_data and u != v
                is_self_loop = (u == v)

                if is_self_loop:
                    x, y = pos[u]
                    loop_size = 0.30
                    dx, dy = loop_size, loop_size * 0.9
                    verts = [(x, y), (x + dx, y + dy), (x - dx, y + dy), (x, y)]
                    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
                    path = Path(verts, codes)
                    patch = PathPatch(path, edgecolor="#555555", linewidth=1.4, facecolor="none", zorder=1.5)
                    plt.gca().add_patch(patch)
                    plt.text(x, y + dy * 0.55, full_text, ha="center", va="center", fontsize=8, color="darkblue",
                             bbox=dict(facecolor="white", edgecolor="lightgray", alpha=0.9, boxstyle="round,pad=0.15"))
                    continue

                x1, y1 = pos[u]
                x2, y2 = pos[v]
                if is_bidirectional:
                    rad = 0.2
                    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], connectionstyle=f"arc3,rad={rad}", 
                                           arrowstyle="-|>", arrowsize=25, edge_color="#555555", width=1.5, node_size=NODE_SIZE)
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    vx, vy = x2 - x1, y2 - y1
                    dist = math.sqrt(vx**2 + vy**2) or 1
                    nx_vec, ny_vec = vy / dist, -vx / dist
                    offset = rad * dist * 0.6
                    plt.text(mx + nx_vec * offset, my + ny_vec * offset, full_text, ha='center', va='center', fontsize=8, color='darkblue',
                             bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, boxstyle='round,pad=0.2'))
                else:
                    nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], arrowstyle="-|>", arrowsize=25, edge_color="#555555", width=1.5, node_size=NODE_SIZE)
                    plt.text((x1 + x2) / 2, (y1 + y2) / 2, full_text, ha='center', va='center', fontsize=8, color='darkblue',
                             bbox=dict(facecolor='white', edgecolor='lightgray', alpha=0.9, boxstyle='round,pad=0.2'))

            plt.title(title, fontsize=14, fontweight='bold')
            plt.axis("off")
            plt.tight_layout()
            plt.show()
        except Exception as e:
            _get_logger().error(f"Failed to draw filtered model graph: {e}")