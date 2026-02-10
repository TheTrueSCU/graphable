from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
from logging import getLogger
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
