"""
Lattice and Algebraic Structures Module.

This module defines classes for representing Complete Distributive Residuated Lattices, and Twist Structures. 
It provides methods for algebraic operations (meet, join, implication) and visualization.
"""

from typing import Set, Dict, Tuple, Optional, List
from collections import defaultdict

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

def _get_logger():
    from services.logging_service import get_logger
    return get_logger("MathObjects")


def _compute_hasse_layout(G):
    """
    Computes a layout for a Hasse Diagram to minimize crossings.
    Uses the Barycenter Heuristic: nodes are placed horizontally based on 
    the average position of their predecessors (children in the lattice).
    """
    if not G.nodes: return {}

    layers = {}
    try:
        sorted_nodes = list(nx.topological_sort(G))
    except:
        return nx.spring_layout(G)

    for n in sorted_nodes:
        preds = list(G.predecessors(n))
        if preds:
            layers[n] = max(layers[p] for p in preds) + 1
        else:
            layers[n] = 0

    layer_nodes = defaultdict(list)
    for n, l in layers.items():
        layer_nodes[l].append(n)
        
    max_layer = max(layers.values())
    pos = {}
    
    layer_nodes[0].sort(key=lambda x: str(x))
    width = len(layer_nodes[0])
    for i, node in enumerate(layer_nodes[0]):
        pos[node] = (i - width / 2.0) * 1.5

    for l in range(1, max_layer + 1):
        node_order = []
        for node in layer_nodes[l]:
            preds = list(G.predecessors(node))
            if preds:
                avg_x = sum(pos[p] for p in preds) / len(preds)
            else:
                avg_x = 0 
            node_order.append((node, avg_x))
        
        node_order.sort(key=lambda x: x[1])
        
        current_nodes = [n for n, x in node_order]
        width = len(current_nodes)
        for i, node in enumerate(current_nodes):
            pos[node] = (i - width / 2.0) * 1.5

    final_pos = {}
    for node, x in pos.items():
        final_pos[node] = (x, layers[node])
        
    return final_pos

def _to_node_repr(element):
    if isinstance(element, tuple):
        return ",".join(str(e).strip("' ") for e in element)
    return str(element).replace("'", "").replace(" ", "")


class Lattice:
    """
    Represents a lattice with elements, a partial order, meet, join, 
    and an explicit implication mapping.
    """

    def __init__(
        self,
        name: str,
        elements: Set[str],
        relations: Set[Tuple[str, str]],
        implication_map: Optional[Dict[Tuple[str, str], str]] = None
    ):
        self.name = name
        self.elements = set(elements)
        self.relations = set(relations)
        self.implication_map = implication_map if implication_map is not None else {}

        if not self._check_is_lattice():
            raise ValueError(f"The object '{name}' is not a valid lattice.")

        if not self._is_distributive():
            raise ValueError(f"The object '{name}' is not a distributive lattice.")

        if self.implication_map and not self._is_residuated():
            raise ValueError(f"The object '{name}' does not satisfy the residuation property.")

        self.bottom = self.meet_set(self.elements)
        self.top = self.join_set(self.elements)

    def is_less_than_or_equal(self, a: str, b: str) -> bool:
        return (a, b) in self.relations

    def join(self, a: str, b: str) -> str:
        if a not in self.elements or b not in self.elements:
            raise ValueError(f"Elements '{a}' or '{b}' not in the lattice.")
        upper_bounds = {
            x for x in self.elements 
            if self.is_less_than_or_equal(a, x) and self.is_less_than_or_equal(b, x)
        }
        if not upper_bounds:
            raise ValueError(f"No common upper bounds found for '{a}' and '{b}'.")
        for x in upper_bounds:
            if all(self.is_less_than_or_equal(x, y) for y in upper_bounds):
                return x
        raise ValueError(f"No unique Join found for '{a}' and '{b}'.")

    def meet(self, a: str, b: str) -> str:
        if a not in self.elements or b not in self.elements:
            raise ValueError(f"Elements '{a}' or '{b}' not in the lattice.")
        lower_bounds = {
            x for x in self.elements 
            if self.is_less_than_or_equal(x, a) and self.is_less_than_or_equal(x, b)
        }
        if not lower_bounds:
            raise ValueError(f"No common lower bounds found for '{a}' and '{b}'.")
        for x in lower_bounds:
            if all(self.is_less_than_or_equal(y, x) for y in lower_bounds):
                return x
        raise ValueError(f"No unique Meet found for '{a}' and '{b}'.")

    def implication(self, a: str, b: str) -> Optional[str]:
        return self.implication_map.get((a, b))

    def meet_set(self, subset: Optional[Set[str]] = None) -> str:
        if subset is None: subset = set()
        subset_list = list(subset)
        if not subset_list: return self.top
        lower = subset_list[0]
        for element in subset_list:
            lower = self.meet(lower, element)
        return lower

    def join_set(self, subset: Optional[Set[str]] = None) -> str:
        if subset is None: subset = set()
        subset_list = list(subset)
        if not subset_list: return self.bottom
        greatest = subset_list[0]
        for element in subset_list:
            greatest = self.join(greatest, element)
        return greatest

    def _check_is_lattice(self) -> bool:
        try:
            for x in self.elements:
                for y in self.elements:
                    self.meet(x, y)
                    self.join(x, y)
            return True
        except ValueError as e:
            _get_logger().error(f"Lattice integrity check failed for '{self.name}': {e}")
            return False

    def _is_distributive(self):
        check = False
        for x in self.elements:
            for y in self.elements:
                for z in self.elements:
                    value1 = self.meet(x, self.join(y, z))
                    value2 = self.join(self.meet(x, y), self.meet(x, z))
                    value3 = self.join(x, self.meet(y, z))
                    value4 = self.meet(self.join(x, y), self.join(x, z))

                    if (value1 == value2) and (value3 == value4):
                        check = True
                    else:
                        return False
        return check

    def _is_residuated(self) -> bool:
        for x in self.elements:
            for y in self.elements:
                xy_meet = self.meet(x, y)
                for z in self.elements:
                    left_cond = self.is_less_than_or_equal(xy_meet, z)
                    imp_xz = self.implication(x, z)
                    right_cond = self.is_less_than_or_equal(y, imp_xz)
                    
                    if left_cond != right_cond:
                        return False
        return True

    def draw_hasse(self) -> None:
        if not VISUALIZATION_AVAILABLE: 
            _get_logger().warning("Visualization unavailable: networkx or matplotlib missing.")
            return
        if not self.elements: return
        
        G = nx.DiGraph()
        G.add_nodes_from([_to_node_repr(e) for e in self.elements])
        
        edges = (self.relations if hasattr(self, 'relations') else self.truth_relation)
        clean_edges = [(_to_node_repr(a), _to_node_repr(b)) for a, b in edges if a != b]
        
        G.add_edges_from(clean_edges)

        if list(nx.simple_cycles(G)):
            _get_logger().error(f"Hasse Diagram for {self.name} contains cycles.")
            return

        try:
            TR = nx.transitive_reduction(G)
        except Exception as e:
            _get_logger().warning(f"Transitive reduction failed for {self.name}, using raw graph: {e}")
            TR = G
        pos = _compute_hasse_layout(TR)

        plt.figure(figsize=(8, 10))
        plt.title(f"Hasse Diagram: {self.name}")

        labels = {node: node for node in TR.nodes()}
        max_len = max((len(l) for l in labels.values()), default=1)
        node_size = 1000 + (max_len * 300)

        nx.draw_networkx_nodes(TR, pos, node_size=node_size, node_color="#A0CBE2", edgecolors="black")
        nx.draw_networkx_labels(TR, pos, labels=labels, font_size=10, font_weight="bold")
        nx.draw_networkx_edges(TR, pos, arrows=False, width=1.5, edge_color="gray")
        
        plt.axis("off")
        plt.tight_layout()
        plt.show(block=False)

    def __repr__(self) -> str:
        return f"{self.name}"


class TwistStructure:
    def __init__(self, lattice: Lattice):
        if not isinstance(lattice, Lattice):
            raise TypeError("Argument must be a Lattice.")
        
        self.lattice = lattice
        self.name = lattice.name
        self.elements = self._build_elements()
        self.truth_relation = self._build_truth_order()
        self.qntt_info_relation = self._build_quantity_info_order()

    def _build_elements(self) -> Set[Tuple[str, str]]:
        return {
            (e1, e2) 
            for e1 in self.lattice.elements 
            for e2 in self.lattice.elements
        }

    def _build_truth_order(self) -> Set[Tuple[Tuple[str, str], Tuple[str, str]]]:
        relation = set()
        l = self.lattice
        for p1 in self.elements:
            for p2 in self.elements:
                if l.is_less_than_or_equal(p1[0], p2[0]) and l.is_less_than_or_equal(p2[1], p1[1]):
                    relation.add((p1, p2))
        return relation

    def _build_quantity_info_order(self) -> Set[Tuple[Tuple[str, str], Tuple[str, str]]]:
        relation = set()
        l = self.lattice
        for p1 in self.elements:
            for p2 in self.elements:
                if l.is_less_than_or_equal(p1[0], p2[0]) and l.is_less_than_or_equal(p1[1], p2[1]):
                    relation.add((p1, p2))
        return relation
    
    def toposort_twist_elements(self):
        from collections import defaultdict, deque

        successors = defaultdict(set)
        predecessors = defaultdict(set)

        for a, b in self.truth_relation:
            if a != b:
                successors[a].add(b)
                predecessors[b].add(a)

        for e in self.elements:
            successors[e]
            predecessors[e]

        queue = deque(sorted(
            [e for e in self.elements if not predecessors[e]],
            key=str
        ))

        result = []

        while queue:
            e = queue.popleft()
            result.append(e)
            for s in sorted(successors[e], key=str):
                predecessors[s].remove(e)
                if not predecessors[s]:
                    queue.append(s)

        return result

    def implication(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        l = self.lattice
        t1, f1 = pair1
        t2, f2 = pair2
        imp_t1_t2 = l.implication(t1, t2)
        imp_f2_f1 = l.implication(f2, f1)
        if imp_t1_t2 is None or imp_f2_f1 is None:
            raise ValueError("Implication definition missing in base lattice.")
        meet_imp = l.meet(imp_t1_t2, imp_f2_f1)
        meet_t1_f2 = l.meet(t1, f2)
        return (meet_imp, meet_t1_f2)

    def consensus(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        l = self.lattice
        meet_t = l.meet(pair1[0], pair2[0])
        meet_f = l.meet(pair1[1], pair2[1]) 
        return (meet_t, meet_f)

    def residue_meet(self, pair1: Tuple[str, str], pair2: Tuple[str, str]) -> Tuple[str, str]:
        l = self.lattice
        t1, f1 = pair1
        t2, f2 = pair2
        meet_t = l.meet(t1, t2)
        imp1 = l.implication(t1, f2)
        imp2 = l.implication(t2, f1)
        if imp1 is None or imp2 is None:
            raise ValueError("Implication definition missing in base lattice for residue_meet.")
        meet_imp = l.meet(imp1, imp2)
        return (meet_t, meet_imp)

    def negation(self, pair): 
        return (pair[1], pair[0])
        
    def weak_meet(self, pair1, pair2): 
        l = self.lattice
        return (l.meet(pair1[0], pair2[0]), l.join(pair1[1], pair2[1]))
        
    def weak_join(self, pair1, pair2):
        l = self.lattice
        return (l.join(pair1[0], pair2[0]), l.meet(pair1[1], pair2[1]))
        
    def accept_all(self, pair1, pair2):
        l = self.lattice
        return (l.join(pair1[0], pair2[0]), l.join(pair1[1], pair2[1]))

    def weak_meet_set(self, pairs: List[Tuple[str, str]]) -> Tuple[str, str]:
        if not pairs:
            return (self.lattice.top, self.lattice.bottom)
        t_list = [p[0] for p in pairs]
        f_list = [p[1] for p in pairs]
        final_t = self.lattice.meet_set(set(t_list))
        final_f = self.lattice.join_set(set(f_list))
        return (final_t, final_f)

    def weak_join_set(self, pairs: List[Tuple[str, str]]) -> Tuple[str, str]:
        if not pairs:
            return (self.lattice.bottom, self.lattice.top)
        t_list = [p[0] for p in pairs]
        f_list = [p[1] for p in pairs]
        final_t = self.lattice.join_set(set(t_list))
        final_f = self.lattice.meet_set(set(f_list))
        return (final_t, final_f)
    
    def draw_hasse(self) -> None:
        if not VISUALIZATION_AVAILABLE: return
        if not self.elements: return
        G = nx.DiGraph()
        G.add_nodes_from([_to_node_repr(e) for e in self.elements])
        
        clean_edges = [(_to_node_repr(a), _to_node_repr(b)) for a, b in self.truth_relation if a != b]
        G.add_edges_from(clean_edges)

        if list(nx.simple_cycles(G)):
            _get_logger().error("TwistStructure Hasse Diagram contains cycles.")
            return

        try:
            TR = nx.transitive_reduction(G)
        except Exception as e:
            _get_logger().warning(f"Transitive reduction failed, using raw graph: {e}")
            TR = G

        pos = _compute_hasse_layout(TR)

        plt.figure(figsize=(8, 10))
        plt.title(f"Hasse Diagram: {self.name}")

        labels = {node: str(node).replace("'", "") for node in TR.nodes()}
        max_len = max((len(l) for l in labels.values()), default=1)
        node_size = 1000 + (max_len * 300)

        nx.draw_networkx_nodes(TR, pos, node_size=node_size, node_color="#A0CBE2", edgecolors="black")
        nx.draw_networkx_labels(TR, pos, labels=labels, font_size=10, font_weight="bold")
        nx.draw_networkx_edges(TR, pos, arrows=False, width=1.5, edge_color="gray")
        
        plt.axis("off")
        plt.tight_layout()
        plt.show(block=False)