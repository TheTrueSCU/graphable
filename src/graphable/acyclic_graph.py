from __future__ import annotations

import copy
from logging import getLogger
from typing import Any, Callable

from .errors import GraphCycleError
from .graph_base import GraphBase
from .graphable import Graphable

logger = getLogger(__name__)


class AcyclicGraph[T: Graphable[Any]](GraphBase[T]):
    """
    Represents a Directed Acyclic Graph (DAG) of Graphable nodes.
    Enforces no cycles.
    """

    def __init__(self, initial: set[T] | list[T] | None = None, discover: bool = False):
        """
        Initialize an AcyclicGraph.

        Raises:
            GraphCycleError: If the initial set of nodes contains a cycle.
        """
        self._topological_order: list[T] | None = None
        self._parallel_topological_order: list[set[T]] | None = None
        super().__init__(initial=initial, discover=discover)
        self.check_cycles()

    def _invalidate_cache(self) -> None:
        super()._invalidate_cache()
        self._topological_order = None
        self._parallel_topological_order = None

    def __iter__(self):
        """Iterate over nodes in topological order."""
        return iter(self.topological_order())

    def check_cycles(self) -> None:
        """
        Check for cycles in the graph.

        Raises:
            GraphCycleError: If a cycle is detected.
        """
        from graphlib import CycleError, TopologicalSorter

        try:
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            sorter.prepare()
        except CycleError as e:
            cycle = list(e.args[1]) if len(e.args) > 1 else None
            raise GraphCycleError(f"Cycle detected in graph: {e}", cycle=cycle) from e

    def add_edge(self, node: T, dependent: T, **attributes: Any) -> None:
        """
        Add a directed edge from node to dependent, enforcing acyclicity.

        Raises:
            GraphCycleError: If adding the edge would create a cycle.
        """
        if node == dependent:
            raise GraphCycleError(
                f"Self-loop detected: node '{node.reference}' cannot depend on itself.",
                cycle=[node, node],
            )

        if path := dependent.find_path(node):
            cycle = path + [dependent]
            raise GraphCycleError(
                f"Adding edge '{node.reference}' -> '{dependent.reference}' would create a cycle.",
                cycle=cycle,
            )

        super().add_edge(node, dependent, **attributes)

    def add_node(self, node: T) -> bool:
        """
        Add a node to the graph, enforcing acyclicity.

        Raises:
            GraphCycleError: If the node is part of an existing cycle.
        """
        if node in self._nodes:
            return False

        if cycle := node.find_path(node):
            raise GraphCycleError(
                f"Node '{node.reference}' is part of an existing cycle.", cycle=cycle
            )

        return super().add_node(node)

    def topological_order(self) -> list[T]:
        """Get nodes in topological order."""
        if self._topological_order is None:
            from graphlib import TopologicalSorter

            logger.debug("Calculating topological order.")
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            self._topological_order = [
                node for node in sorter.static_order() if node in self._nodes
            ]
        return self._topological_order

    def topological_order_filtered(self, fn: Callable[[T], bool]) -> list[T]:
        """Get filtered list of nodes in topological order."""
        return [node for node in self.topological_order() if fn(node)]

    def topological_order_tagged(self, tag: str) -> list[T]:
        """Get list of nodes with a specific tag in topological order."""
        return [node for node in self.topological_order() if node.is_tagged(tag)]

    def parallelized_topological_order(self) -> list[set[T]]:
        """Get nodes in topological order, grouped for parallel processing."""
        if self._parallel_topological_order is None:
            from graphlib import TopologicalSorter

            logger.debug("Calculating parallel topological order.")
            self._parallel_topological_order = []
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            sorter.prepare()
            while sorter.is_active():
                ready = sorter.get_ready()
                if not ready:
                    break
                # Filter to only include nodes that are actually in this graph
                filtered_ready = {node for node in ready if node in self._nodes}
                if filtered_ready:
                    self._parallel_topological_order.append(filtered_ready)
                sorter.done(*ready)
        return self._parallel_topological_order

    def parallelized_topological_order_filtered(
        self, fn: Callable[[T], bool]
    ) -> list[set[T]]:
        """Get filtered sets of nodes in parallelized topological order."""
        result = []
        for group in self.parallelized_topological_order():
            filtered_group = {node for node in group if fn(node)}
            if filtered_group:
                result.append(filtered_group)
        return result

    def parallelized_topological_order_tagged(self, tag: str) -> list[set[T]]:
        """Get sets of nodes with a specific tag in parallelized topological order."""
        return self.parallelized_topological_order_filtered(lambda n: n.is_tagged(tag))

    def cpm_analysis(self) -> dict[T, dict[str, float]]:
        """Perform Critical Path Method (CPM) analysis."""
        topo_order = self.topological_order()
        if not topo_order:
            return {}

        analysis: dict[T, dict[str, float]] = {
            node: {"ES": 0.0, "EF": 0.0, "LS": 0.0, "LF": 0.0, "slack": 0.0}
            for node in topo_order
        }

        # Forward Pass
        for node in topo_order:
            max_ef = 0.0
            for dep in node.depends_on:
                if dep in analysis:
                    max_ef = max(max_ef, analysis[dep]["EF"])
            analysis[node]["ES"] = max_ef
            analysis[node]["EF"] = max_ef + node.duration

        # Backward Pass
        max_total_ef = max(analysis[node]["EF"] for node in topo_order)
        for node in reversed(topo_order):
            if not node.dependents or all(d not in analysis for d in node.dependents):
                min_ls = max_total_ef
            else:
                min_ls = min(
                    analysis[dep]["LS"] for dep in node.dependents if dep in analysis
                )
            analysis[node]["LF"] = min_ls
            analysis[node]["LS"] = min_ls - node.duration
            analysis[node]["slack"] = analysis[node]["LF"] - analysis[node]["EF"]

        return analysis

    def critical_path(self) -> list[T]:
        """Identify nodes on the critical path."""
        analysis = self.cpm_analysis()
        return [
            node
            for node in self.topological_order()
            if abs(analysis[node]["slack"]) < 1e-9
        ]

    def longest_path(self) -> list[T]:
        """Find the longest path based on node durations."""
        analysis = self.cpm_analysis()
        cp_nodes = {
            node for node, vals in analysis.items() if abs(vals["slack"]) < 1e-9
        }
        if not cp_nodes:
            return []

        current = None
        for node in self.sources:
            if node in cp_nodes:
                current = node
                break
        if current is None:
            current = sorted(
                list(cp_nodes), key=lambda n: self.topological_order().index(n)
            )[0]

        path = [current]
        while True:
            next_node = None
            for dep in current.dependents:
                if (
                    dep in cp_nodes
                    and abs(analysis[dep]["ES"] - analysis[current]["EF"]) < 1e-9
                ):
                    next_node = dep
                    break
            if next_node:
                path.append(next_node)
                current = next_node
            else:
                break
        return path

    def transitive_closure(self) -> AcyclicGraph[T]:
        """Compute the transitive closure of this graph."""
        logger.debug("Calculating transitive closure.")
        node_map = {node: copy.copy(node) for node in self._nodes}
        for n in node_map.values():
            n._dependents = {}
            n._depends_on = {}

        new_graph = AcyclicGraph(set(node_map.values()))
        for u in self._nodes:
            for v in self.descendants(u):
                new_graph.add_edge(node_map[u], node_map[v])
        return new_graph

    def transitive_reduction(self) -> AcyclicGraph[T]:
        """Compute the transitive reduction of this DAG."""
        logger.debug("Calculating transitive reduction.")
        node_map: dict[T, T] = {}
        for node in self._nodes:
            new_node = copy.copy(node)
            new_node._dependents = {}
            new_node._depends_on = {}
            new_node._tags = set(node.tags)
            node_map[node] = new_node

        redundant_edges: set[tuple[T, T]] = set()
        for u in self._nodes:
            for v in u.dependents:
                if any(w.find_path(v) for w in u.dependents if w != v):
                    redundant_edges.add((u, v))

        new_graph = AcyclicGraph(set(node_map.values()))
        for u in self._nodes:
            for v in u.dependents:
                if (u, v) not in redundant_edges:
                    attrs = u.edge_attributes(v)
                    new_graph.add_edge(node_map[u], node_map[v], **attrs)

        logger.info(
            f"Transitive reduction complete. Removed {len(redundant_edges)} redundant edges."
        )
        return new_graph
