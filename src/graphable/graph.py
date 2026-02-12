from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from .errors import GraphConsistencyError, GraphCycleError
from .graphable import Graphable

logger = getLogger(__name__)


def graph[T: Graphable[Any]](contains: list[T]) -> Graph[T]:
    """
    Constructs a Graph containing the given nodes and all their connected dependencies/dependents.
    It traverses the graph both up (dependencies) and down (dependents) from the initial nodes.

    Args:
        contains (list[T]): A list of initial nodes to start the graph construction from.

    Returns:
        Graph[T]: A Graph object containing all reachable nodes.
    """
    logger.debug(f"Building graph from {len(contains)} initial nodes.")

    def go_down(node: T, nodes: set[T]) -> None:
        """
        Recursively traverse down the graph to find all dependent nodes.

        Args:
            node (T): The current node to traverse from.
            nodes (set[T]): The set of nodes found so far.
        """
        for down_node in node.dependents:
            if down_node in nodes:
                continue

            nodes.add(down_node)
            go_down(down_node, nodes)

    def go_up(node: T, nodes: set[T]) -> None:
        """
        Recursively traverse up the graph to find all dependency nodes.

        Args:
            node (T): The current node to traverse from.
            nodes (set[T]): The set of nodes found so far.
        """
        for up_node in node.depends_on:
            if up_node in nodes:
                continue

            nodes.add(up_node)
            go_up(up_node, nodes)

    nodes: set[T] = set(contains)
    for node in contains:
        go_up(node, nodes)
        go_down(node, nodes)

    logger.info(f"Graph built with {len(nodes)} total nodes.")
    return Graph(nodes)


class Graph[T: Graphable[Any]]:
    """
    Represents a graph of Graphable nodes.
    """

    def __init__(self, initial: set[T] | None = None):
        """
        Initialize a Graph.

        Args:
            initial (set[T] | None): An optional set of initial nodes.

        Raises:
            GraphCycleError: If the initial set of nodes contains a cycle.
        """
        self._nodes: set[T] = initial if initial else set[T]()
        self._topological_order: list[T] | None = None

        if self._nodes:
            self.check_consistency()
            self.check_cycles()

    def __contains__(self, item: Any) -> bool:
        """
        Check if a node or its reference is in the graph.

        Args:
            item (Any): Either a Graphable node or a reference object.

        Returns:
            bool: True if present, False otherwise.
        """
        if isinstance(item, Graphable):
            return item in self._nodes

        return any(node.reference == item for node in self._nodes)

    def __getitem__(self, reference: Any) -> T:
        """
        Get a node by its reference.

        Args:
            reference (Any): The reference object to search for.

        Returns:
            T: The Graphable node.

        Raises:
            KeyError: If no node with the given reference exists.
        """
        for node in self._nodes:
            if node.reference == reference:
                return node
        raise KeyError(f"No node found with reference: {reference}")

    def __iter__(self):
        """
        Iterate over nodes in topological order.
        """
        return iter(self.topological_order())

    def __len__(self) -> int:
        """
        Get the number of nodes in the graph.
        """
        return len(self._nodes)

    def check_cycles(self) -> None:
        """
        Check for cycles in the graph.

        Raises:
            GraphCycleError: If a cycle is detected.
        """
        try:
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            sorter.prepare()
        except CycleError as e:
            # graphlib.CycleError args: (message, cycle_tuple)
            cycle = list(e.args[1]) if len(e.args) > 1 else None
            raise GraphCycleError(f"Cycle detected in graph: {e}", cycle=cycle) from e

    def check_consistency(self) -> None:
        """
        Check for consistency between depends_on and dependents for all nodes in the graph.

        Raises:
            GraphConsistencyError: If an inconsistency is detected.
        """
        for node in self._nodes:
            self._check_node_consistency(node)

    def _check_node_consistency(self, node: T) -> None:
        """
        Check for consistency between depends_on and dependents for a single node.

        Args:
            node (T): The node to check.

        Raises:
            GraphConsistencyError: If an inconsistency is detected.
        """
        # Check dependencies: if node depends on X, X must have node as dependent
        for dep in node.depends_on:
            if node not in dep.dependents:
                raise GraphConsistencyError(
                    f"Inconsistency: Node '{node.reference}' depends on '{dep.reference}', "
                    f"but '{dep.reference}' does not list '{node.reference}' as a dependent."
                )
        # Check dependents: if node has dependent Y, Y must depend on node
        for sub in node.dependents:
            if node not in sub.depends_on:
                raise GraphConsistencyError(
                    f"Inconsistency: Node '{node.reference}' has dependent '{sub.reference}', "
                    f"but '{sub.reference}' does not depend on '{node.reference}'."
                )

    def add_edge(self, node: T, dependent: T) -> None:
        """
        Add a directed edge from node to dependent.
        Also adds the nodes to the graph if they are not already present.

        Args:
            node (T): The source node (dependency).
            dependent (T): The target node (dependent).

        Raises:
            GraphCycleError: If adding the edge would create a cycle.
        """
        if node == dependent:
            raise GraphCycleError(
                f"Self-loop detected: node '{node.reference}' cannot depend on itself.",
                cycle=[node, node],
            )

        # Check if adding this edge creates a cycle.
        # A cycle is created if there is already a path from 'dependent' to 'node'.
        if path := dependent.find_path(node):
            cycle = path + [dependent]
            raise GraphCycleError(
                f"Adding edge '{node.reference}' -> '{dependent.reference}' would create a cycle.",
                cycle=cycle,
            )

        self.add_node(node)
        self.add_node(dependent)

        node._add_dependent(dependent)
        dependent._add_depends_on(node)
        logger.debug(f"Added edge: {node.reference} -> {dependent.reference}")

        # Invalidate cache
        if self._topological_order is not None:
            self._topological_order = None

    def add_node(self, node: T) -> bool:
        """
        Add a node to the graph.

        Args:
            node (T): The node to add.

        Returns:
            bool: True if the node was added (was not already present), False otherwise.

        Raises:
            GraphCycleError: If the node is part of an existing cycle.
        """
        if node in self._nodes:
            return False

        # If the node is already part of a cycle (linked externally), adding it might be invalid
        # if we want to enforce DAG.
        if cycle := node.find_path(node):
            raise GraphCycleError(
                f"Node '{node.reference}' is part of an existing cycle.", cycle=cycle
            )

        self._check_node_consistency(node)
        self._nodes.add(node)
        logger.debug(f"Added node: {node.reference}")

        if self._topological_order is not None:
            self._topological_order = None

        return True

    def remove_edge(self, node: T, dependent: T) -> None:
        """
        Remove a directed edge from node to dependent.

        Args:
            node (T): The source node.
            dependent (T): The target node.
        """
        if node in self._nodes and dependent in self._nodes:
            node._remove_dependent(dependent)
            dependent._remove_depends_on(node)
            logger.debug(f"Removed edge: {node.reference} -> {dependent.reference}")

            if self._topological_order is not None:
                self._topological_order = None

    def remove_node(self, node: T) -> None:
        """
        Remove a node and all its connected edges from the graph.

        Args:
            node (T): The node to remove.
        """
        if node in self._nodes:
            # Remove from all nodes it depends on
            for dep in list(node.depends_on):
                dep._remove_dependent(node)

            # Remove from all nodes that depend on it
            for sub in list(node.dependents):
                sub._remove_depends_on(node)

            self._nodes.remove(node)
            logger.debug(f"Removed node: {node.reference}")

            if self._topological_order is not None:
                self._topological_order = None

    def ancestors(self, node: T) -> set[T]:
        """
        Get all nodes that the given node depends on, recursively.

        Args:
            node (T): The starting node.

        Returns:
            set[T]: A set of all ancestor nodes.
        """
        ancestors: set[T] = set()

        def discover(current: T):
            for dep in current.depends_on:
                if dep not in ancestors:
                    ancestors.add(dep)
                    discover(dep)

        discover(node)
        return ancestors

    def descendants(self, node: T) -> set[T]:
        """
        Get all nodes that depend on the given node, recursively.

        Args:
            node (T): The starting node.

        Returns:
            set[T]: A set of all descendant nodes.
        """
        descendants: set[T] = set()

        def discover(current: T):
            for sub in current.dependents:
                if sub not in descendants:
                    descendants.add(sub)
                    discover(sub)

        discover(node)
        return descendants

    @property
    def sinks(self) -> list[T]:
        """
        Get all sink nodes (nodes with no dependents).

        Returns:
            list[T]: A list of sink nodes.
        """
        return [node for node in self._nodes if 0 == len(node.dependents)]

    @property
    def sources(self) -> list[T]:
        """
        Get all source nodes (nodes with no dependencies).

        Returns:
            list[T]: A list of source nodes.
        """
        return [node for node in self._nodes if 0 == len(node.depends_on)]

    def subgraph_filtered(self, fn: Callable[[T], bool]) -> Graph[T]:
        """
        Create a new subgraph containing only nodes that satisfy the predicate.

        Args:
            fn (Callable[[T], bool]): The predicate function.

        Returns:
            Graph[T]: A new Graph containing the filtered nodes.
        """
        logger.debug("Creating filtered subgraph.")
        return graph([node for node in self._nodes if fn(node)])

    def subgraph_tagged(self, tag: str) -> Graph[T]:
        """
        Create a new subgraph containing only nodes with the specified tag.

        Args:
            tag (str): The tag to filter by.

        Returns:
            Graph[T]: A new Graph containing the tagged nodes.
        """
        logger.debug(f"Creating subgraph for tag: {tag}")
        return graph([node for node in self._nodes if node.is_tagged(tag)])

    def topological_order(self) -> list[T]:
        """
        Get the nodes in topological order.

        Returns:
            list[T]: A list of nodes sorted topologically.
        """
        if self._topological_order is None:
            logger.debug("Calculating topological order.")
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            self._topological_order = list(sorter.static_order())

        return self._topological_order

    def topological_order_filtered(self, fn: Callable[[T], bool]) -> list[T]:
        """
        Get a filtered list of nodes in topological order.

        Args:
            fn (Callable[[T], bool]): The predicate function.

        Returns:
            list[T]: Filtered topologically sorted nodes.
        """
        return [node for node in self.topological_order() if fn(node)]

    def topological_order_tagged(self, tag: str) -> list[T]:
        """
        Get a list of nodes with a specific tag in topological order.

        Args:
            tag (str): The tag to filter by.

        Returns:
            list[T]: Tagged topologically sorted nodes.
        """
        return [node for node in self.topological_order() if node.is_tagged(tag)]

    def to_networkx(self):
        """
        Convert this graph to a networkx.DiGraph.
        Requires 'networkx' to be installed.

        Returns:
            networkx.DiGraph: The converted directed graph.
        """
        from .views.networkx import to_networkx

        return to_networkx(self)

    def transitive_reduction(self) -> Graph[T]:
        """
        Compute the transitive reduction of this DAG.
        A transitive reduction of a directed acyclic graph G is a graph G' with the same nodes
        and the same reachability as G, but with as few edges as possible.

        Returns:
            Graph[T]: A new Graph instance containing the same nodes (cloned) but with redundant edges removed.
        """
        import copy

        logger.debug("Calculating transitive reduction.")

        # 1. Clone nodes without edges to avoid modifying the original graph.
        node_map: dict[T, T] = {}
        for node in self._nodes:
            new_node = copy.copy(node)
            # Reset internal edge tracking
            new_node._dependents = set()
            new_node._depends_on = set()
            # Manually clone tags to avoid shared state
            new_node._tags = set(node.tags)
            node_map[node] = new_node

        # 2. Identify redundant edges.
        # An edge (u, v) is redundant if there exists a path from u to v of length > 1.
        redundant_edges: set[tuple[T, T]] = set()
        for u in self._nodes:
            for v in u.dependents:
                # Check if v is reachable from u through any other neighbor w.
                if any(w.find_path(v) for w in u.dependents if w != v):
                    redundant_edges.add((u, v))

        # 3. Construct the new graph with non-redundant edges.
        new_graph = Graph(set(node_map.values()))
        for u in self._nodes:
            for v in u.dependents:
                if (u, v) not in redundant_edges:
                    new_graph.add_edge(node_map[u], node_map[v])

        logger.info(
            f"Transitive reduction complete. Removed {len(redundant_edges)} redundant edges."
        )
        return new_graph

    def render(
        self,
        view_fnc: Callable[..., str],
        transitive_reduction: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Render the graph using a view function.

        Args:
            view_fnc: The view function to use (e.g., create_topology_mermaid_mmd).
            transitive_reduction: If True, render the transitive reduction of the graph.
            **kwargs: Additional arguments passed to the view function.

        Returns:
            str: The rendered representation.
        """
        target = self.transitive_reduction() if transitive_reduction else self
        return view_fnc(target, **kwargs)

    def export(
        self,
        export_fnc: Callable[..., None],
        output: Path | str,
        transitive_reduction: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Export the graph using an export function.

        Args:
            export_fnc: The export function to use (e.g., export_topology_graphviz_svg).
            output: The output file path.
            transitive_reduction: If True, export the transitive reduction of the graph.
            **kwargs: Additional arguments passed to the export function.
        """
        from pathlib import Path

        target = self.transitive_reduction() if transitive_reduction else self
        export_fnc(target, Path(output), **kwargs)
