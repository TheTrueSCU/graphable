from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
from hashlib import blake2b
from logging import getLogger
from pathlib import Path
from typing import Any, Callable, Iterator

from .enums import Direction, Engine
from .errors import GraphConsistencyError, GraphCycleError
from .graphable import Graphable

logger = getLogger(__name__)


class Graph[T: Graphable[Any]]:
    """
    Represents a graph of Graphable nodes.
    """

    def __init__(self, initial: set[T] | list[T] | None = None, discover: bool = False):
        """
        Initialize a Graph.

        Args:
            initial (set[T] | list[T] | None): An optional set of initial nodes.
            discover (bool): If True, automatically expand the graph to include all
                reachable ancestors and descendants of the initial nodes.

        Raises:
            GraphCycleError: If the initial set of nodes contains a cycle.
        """
        self._nodes: set[T] = set()
        self._topological_order: list[T] | None = None
        self._parallel_topological_order: list[set[T]] | None = None
        self._checksum: str | None = None

        if initial:
            for node in initial:
                self.add_node(node)

            if discover:
                self.discover()

            self.check_consistency()
            self.check_cycles()

    def clone(self, include_edges: bool = False) -> Graph[T]:
        """
        Create a copy of this graph.

        Args:
            include_edges: If True, the new graph will have the same edges as this one.
                If False, the new graph will contain copies of all nodes but with
                no edges between them.

        Returns:
            Graph[T]: A new Graph instance.
        """
        import copy

        logger.debug(f"Cloning graph (include_edges={include_edges}).")
        node_map: dict[T, T] = {}
        for node in self._nodes:
            new_node = copy.copy(node)
            # Reset internal edge tracking
            new_node._dependents = {}
            new_node._depends_on = {}
            # Manually clone tags to avoid shared state
            new_node._tags = set(node.tags)
            node_map[node] = new_node

        new_graph = Graph(set(node_map.values()))

        if include_edges:
            for u in self._nodes:
                for v, attrs in self.neighbors(u, Direction.DOWN):
                    new_graph.add_edge(node_map[u], node_map[v], **attrs)

        return new_graph

    def neighbors(
        self, node: T, direction: Direction = Direction.DOWN
    ) -> Iterator[tuple[T, dict[str, Any]]]:
        """
        Iterate over neighbors within this graph.

        Args:
            node (T): The source node.
            direction: Direction.DOWN for dependents, Direction.UP for dependencies.

        Yields:
            tuple[T, dict[str, Any]]: A (neighbor_node, edge_attributes) tuple.
        """
        neighbors = node.dependents if direction == Direction.DOWN else node.depends_on
        for neighbor in neighbors:
            if neighbor in self._nodes:
                attrs = (
                    node.edge_attributes(neighbor)
                    if direction == Direction.DOWN
                    else neighbor.edge_attributes(node)
                )
                yield neighbor, attrs

    def internal_dependents(self, node: T) -> Iterator[tuple[T, dict[str, Any]]]:
        """Alias for neighbors(node, Direction.DOWN)."""
        return self.neighbors(node, Direction.DOWN)

    def internal_depends_on(self, node: T) -> Iterator[tuple[T, dict[str, Any]]]:
        """Alias for neighbors(node, Direction.UP)."""
        return self.neighbors(node, Direction.UP)

    def discover(self) -> None:
        """
        Traverse the entire connectivity of the current nodes and add any
        reachable ancestors or descendants that are not yet members.
        """
        logger.debug(f"Discovering reachable nodes from {len(self._nodes)} base nodes.")

        new_nodes: set[T] = set()
        for node in list(self._nodes):
            new_nodes.update(
                self._traverse(node, direction=Direction.UP, limit_to_graph=False)
            )
            new_nodes.update(
                self._traverse(node, direction=Direction.DOWN, limit_to_graph=False)
            )

        for node in new_nodes:
            self.add_node(node)

    def _invalidate_cache(self) -> None:
        """Clear all cached calculations for this graph."""
        logger.debug("Invalidating graph cache.")
        self._topological_order = None
        self._parallel_topological_order = None
        self._checksum = None

    def __contains__(self, item: object) -> bool:
        """
        Check if a node or its reference is in the graph.

        Args:
            item (object): Either a Graphable node or a reference object.

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

    def is_equal_to(self, other: object) -> bool:
        """
        Check if this graph is equal to another graph.
        Equality is defined as having the same checksum (structural and metadata-wise).

        Args:
            other: The other object to compare with.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, Graph):
            return False

        return self.checksum() == other.checksum()

    def checksum(self) -> str:
        """
        Calculate a deterministic BLAKE2b checksum of the graph.
        The checksum accounts for all member nodes (references, tags, duration, status)
        and edges (including attributes) between them. External nodes are excluded.

        Returns:
            str: The hexadecimal digest of the graph.
        """
        if self._checksum is not None:
            return self._checksum

        # 1. Sort nodes by reference to ensure deterministic iteration
        sorted_nodes = sorted(self._nodes, key=lambda n: str(n.reference))

        hasher = blake2b()

        for node in sorted_nodes:
            # 2. Add node reference, duration, and status
            hasher.update(str(node.reference).encode())
            hasher.update(f":duration:{node.duration}".encode())
            hasher.update(f":status:{node.status}".encode())

            # 3. Add sorted tags
            for tag in sorted(node.tags):
                hasher.update(f":tag:{tag}".encode())

            # 4. Add sorted dependents (edges) with attributes - Only those in the graph
            internal_dependents = sorted(
                [d for d in node.dependents if d in self._nodes],
                key=lambda n: str(n.reference),
            )
            for dep in internal_dependents:
                hasher.update(f":edge:{dep.reference}".encode())
                # Add edge attributes deterministically
                attrs = node.edge_attributes(dep)
                for key in sorted(attrs.keys()):
                    hasher.update(f":attr:{key}:{attrs[key]}".encode())

        self._checksum = hasher.hexdigest()
        return self._checksum

    def validate_checksum(self, expected: str) -> bool:
        """
        Validate the graph against an expected checksum.

        Args:
            expected (str): The expected BLAKE2b hexadecimal digest.

        Returns:
            bool: True if the checksums match, False otherwise.
        """
        return self.checksum() == expected

    def write_checksum(self, path: Path | str) -> None:
        """
        Write the graph's current checksum to a file.

        Args:
            path: Path to the output checksum file.
        """
        p = Path(path)
        digest = self.checksum()
        logger.info(f"Writing checksum to: {p}")
        with open(p, "w+") as f:
            f.write(digest)

    @staticmethod
    def read_checksum(path: Path | str) -> str:
        """
        Read a checksum from a file.

        Args:
            path: Path to the checksum file.

        Returns:
            str: The checksum string.
        """
        p = Path(path)
        logger.debug(f"Reading checksum from: {p}")
        with open(p, "r") as f:
            return f.read().strip()

    @classmethod
    def read(cls, path: Path | str, **kwargs: Any) -> Graph[Any]:
        """Read a graph from a file, automatically detecting the format."""
        from .parsers.utils import extract_checksum
        from .registry import PARSERS

        p = Path(path)
        ext = p.suffix.lower()
        parser = PARSERS.get(ext)
        if not parser:
            raise ValueError(f"Unsupported extension for reading: {ext}")

        g = parser(p, **kwargs)

        if embedded := extract_checksum(p):
            if not g.validate_checksum(embedded):
                raise ValueError(f"Checksum validation failed for {p}")
        return g

    def write(
        self,
        path: Path | str,
        transitive_reduction: bool = False,
        embed_checksum: bool = False,
        engine: Engine | str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Write the graph to a file, automatically detecting the format.

        Args:
            path: Path to the output file.
            transitive_reduction: If True, perform transitive reduction before writing.
            embed_checksum: If True, embed a BLAKE2b checksum in the output.
            engine: The rendering engine to use for images (.svg, .png).
                If None, it will be auto-detected.
            **kwargs: Additional arguments passed to the specific exporter.
        """
        from .registry import EXPORTERS

        p = Path(path)
        ext = p.suffix.lower()

        # Handle images specifically to allow engine selection/auto-detection
        if ext in (".svg", ".png"):
            from .views.utils import get_image_exporter

            exporter = get_image_exporter(engine)
        else:
            exporter = EXPORTERS.get(ext)

        if not exporter:
            raise ValueError(f"Unsupported extension: {ext}")

        return self.export(exporter, p, transitive_reduction, embed_checksum, **kwargs)

    def parallelized_topological_order(self) -> list[set[T]]:
        """
        Get the nodes in topological order, grouped into sets that can be processed in parallel.
        Only nodes that are members of this graph are included.

        Returns:
            list[set[T]]: A list of sets of member nodes that have no unmet dependencies.
        """
        if self._parallel_topological_order is None:
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

    def subgraph_between(self, source: T, target: T) -> Graph[T]:
        """
        Create a new graph containing all nodes and edges on all paths between source and target.

        Args:
            source (T): The starting node.
            target (T): The ending node.

        Returns:
            Graph[T]: A new Graph instance.
        """
        if source not in self._nodes or target not in self._nodes:
            raise KeyError("Both source and target must be in the graph.")

        # Nodes between U and V are nodes that are descendants of U AND ancestors of V
        descendants = {source} | set(self.descendants(source))
        ancestors = {target} | set(self.ancestors(target))
        between = descendants & ancestors

        return Graph(between)

    def diff_graph(self, other: Graph[T]) -> Graph[T]:
        """
        Create a visualization-friendly diff graph.
        - Nodes in both: grey/default
        - Added nodes: green
        - Removed nodes: red
        - Modified nodes/edges: yellow/orange

        Returns:
            Graph[T]: A merged graph with diff metadata.
        """
        import copy

        merged_nodes_map: dict[Any, T] = {}
        diff_info = self.diff(other)

        def get_or_create(node: T, status: str) -> T:
            ref = node.reference
            if ref not in merged_nodes_map:
                new_node = copy.copy(node)
                new_node._dependents = {}
                new_node._depends_on = {}
                new_node.add_tag(f"diff:{status}")
                # Add visual hints
                color = {"added": "green", "removed": "red", "modified": "orange"}.get(
                    status, "grey"
                )
                new_node.add_tag(f"color:{color}")
                merged_nodes_map[ref] = new_node
            return merged_nodes_map[ref]

        # Add all nodes from both
        for node in self._nodes:
            status = (
                "removed"
                if node.reference in diff_info["removed_nodes"]
                else "unchanged"
            )
            if node.reference in diff_info["modified_nodes"]:
                status = "modified"
            get_or_create(node, status)

        for node in other._nodes:
            status = (
                "added" if node.reference in diff_info["added_nodes"] else "unchanged"
            )
            if node.reference in diff_info["modified_nodes"]:
                status = "modified"
            get_or_create(node, status)

        new_graph = Graph(set(merged_nodes_map.values()))

        # Add edges from self (original)
        for u in self._nodes:
            for v in u.dependents:
                if v not in self._nodes:
                    continue
                edge = (u.reference, v.reference)
                if edge in diff_info["removed_edges"]:
                    new_graph.add_edge(
                        merged_nodes_map[u.reference],
                        merged_nodes_map[v.reference],
                        diff_status="removed",
                        color="red",
                    )
                elif edge in diff_info["modified_edges"]:
                    new_graph.add_edge(
                        merged_nodes_map[u.reference],
                        merged_nodes_map[v.reference],
                        **u.edge_attributes(v),
                        diff_status="modified",
                        color="orange",
                    )
                else:
                    new_graph.add_edge(
                        merged_nodes_map[u.reference],
                        merged_nodes_map[v.reference],
                        **u.edge_attributes(v),
                    )

        # Add edges from other (new)
        for u in other._nodes:
            for v in u.dependents:
                if v not in other._nodes:
                    continue
                edge = (u.reference, v.reference)
                if edge in diff_info["added_edges"]:
                    new_graph.add_edge(
                        merged_nodes_map[u.reference],
                        merged_nodes_map[v.reference],
                        **u.edge_attributes(v),
                        diff_status="added",
                        color="green",
                    )

        return new_graph

    def transitive_closure(self) -> Graph[T]:
        """
        Compute the transitive closure of this graph.
        An edge (u, v) exists in the transitive closure if there is a path from u to v.

        Returns:
            Graph[T]: A new Graph instance representing the transitive closure.
        """
        import copy

        logger.debug("Calculating transitive closure.")
        node_map = {node: copy.copy(node) for node in self._nodes}
        for n in node_map.values():
            n._dependents = {}
            n._depends_on = {}

        new_graph = Graph(set(node_map.values()))
        for u in self._nodes:
            for v in self.descendants(u):
                new_graph.add_edge(node_map[u], node_map[v])

        return new_graph

    def suggest_cycle_breaks(self) -> list[tuple[T, T]]:
        """
        Identify a minimal set of edges to remove to make the graph a Directed Acyclic Graph (DAG).
        Uses a greedy heuristic.

        Returns:
            list[tuple[T, T]]: A list of (source, target) tuples representing suggested edges to remove.
        """
        logger.debug("Suggesting cycle breaks.")
        # Simple heuristic:
        # 1. Take all nodes.
        # 2. Try to order them such that we maximize forward edges.
        # A simple way is to use the order they were added or any arbitrary order
        # and see which edges go 'backwards'.

        nodes = list(self._nodes)
        # We can try to be slightly smarter by using a DFS and finding back-edges
        back_edges = []
        visited = set()
        stack = set()

        def dfs(u):
            visited.add(u)
            stack.add(u)
            for v in u.dependents:
                if v not in self._nodes:
                    continue
                if v in stack:
                    back_edges.append((u, v))
                elif v not in visited:
                    dfs(v)
            stack.remove(u)

        for node in nodes:
            if node not in visited:
                dfs(node)

        return back_edges

    def parallelized_topological_order_filtered(
        self, fn: Callable[[T], bool]
    ) -> list[set[T]]:
        """
        Get a filtered list of nodes in parallelized topological order.

        Args:
            fn (Callable[[T], bool]): The predicate function.

        Returns:
            list[set[T]]: Filtered sets of nodes for parallel processing.
        """
        result = []
        for group in self.parallelized_topological_order():
            filtered_group = {node for node in group if fn(node)}
            if filtered_group:
                result.append(filtered_group)
        return result

    def parallelized_topological_order_tagged(self, tag: str) -> list[set[T]]:
        """
        Get a list of nodes with a specific tag in parallelized topological order.

        Args:
            tag (str): The tag to filter by.

        Returns:
            list[set[T]]: Tagged sets of nodes for parallel processing.
        """
        return self.parallelized_topological_order_filtered(lambda n: n.is_tagged(tag))

    def __eq__(self, other: object) -> bool:
        """
        Compare two graphs for equality.
        """
        return self.is_equal_to(other)

    def __hash__(self) -> int:
        """
        Graphs are hashable by identity to allow them to be used in WeakSets
        (e.g., as observers of Graphable nodes).
        """
        return id(self)

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

    def add_edge(self, node: T, dependent: T, **attributes: Any) -> None:
        """
        Add a directed edge from node to dependent.
        Also adds the nodes to the graph if they are not already present.

        Args:
            node (T): The source node (dependency).
            dependent (T): The target node (dependent).
            **attributes: Edge attributes (e.g., weight, label).

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

        node._add_dependent(dependent, **attributes)
        dependent._add_depends_on(node, **attributes)
        logger.debug(
            f"Added edge: {node.reference} -> {dependent.reference} with attributes {attributes}"
        )

        # Invalidate cache
        self._invalidate_cache()

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
        node._register_observer(self)
        logger.debug(f"Added node: {node.reference}")

        self._invalidate_cache()

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

            self._invalidate_cache()

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
            node._unregister_observer(self)
            logger.debug(f"Removed node: {node.reference}")

            self._invalidate_cache()

    def ancestors(self, node: T) -> Iterator[T]:
        """
        Get an iterator for all nodes that the given node depends on, recursively.

        Args:
            node (T): The starting node.

        Yields:
            T: The next ancestor node.
        """
        return self._traverse(node, direction=Direction.UP, include_start=False)

    def descendants(self, node: T) -> Iterator[T]:
        """
        Get an iterator for all nodes that depend on the given node, recursively.

        Args:
            node (T): The starting node.

        Yields:
            T: The next descendant node.
        """
        return self._traverse(node, direction=Direction.DOWN, include_start=False)

    def bfs(
        self,
        start_node: T,
        direction: Direction = Direction.DOWN,
        limit_to_graph: bool = True,
    ) -> Iterator[T]:
        """
        Perform a breadth-first search (BFS) starting from the given node.

        Args:
            start_node (T): The node to start from.
            direction: Direction.UP for dependencies, Direction.DOWN for dependents.
            limit_to_graph: If True, only return nodes that are members of this graph.

        Yields:
            T: Each reached node in breadth-first order.
        """
        from collections import deque

        if limit_to_graph and start_node not in self._nodes:
            return

        visited: set[T] = {start_node}
        queue: deque[T] = deque([start_node])

        yield start_node

        while queue:
            current = queue.popleft()
            neighbors = (
                current.dependents
                if direction == Direction.DOWN
                else current.depends_on
            )
            for neighbor in neighbors:
                if neighbor not in visited:
                    if limit_to_graph and neighbor not in self._nodes:
                        continue
                    visited.add(neighbor)
                    yield neighbor
                    queue.append(neighbor)

    def dfs(
        self,
        start_node: T,
        direction: Direction = Direction.DOWN,
        limit_to_graph: bool = True,
    ) -> Iterator[T]:
        """
        Perform a depth-first search (DFS) starting from the given node.

        Args:
            start_node (T): The node to start from.
            direction: Direction.UP for dependencies, Direction.DOWN for dependents.
            limit_to_graph: If True, only return nodes that are members of this graph.

        Yields:
            T: Each reached node in depth-first order.
        """
        return self._traverse(
            start_node,
            direction=direction,
            limit_to_graph=limit_to_graph,
            include_start=True,
        )

    def _traverse(
        self,
        start_node: T,
        direction: Direction = Direction.DOWN,
        limit_to_graph: bool = True,
        include_start: bool = False,
    ) -> Iterator[T]:
        """
        Generic depth-first traversal utility.

        Args:
            start_node (T): Node to start from.
            direction: Direction.UP (depends_on) or Direction.DOWN (dependents).
            limit_to_graph: If True, only return nodes that are members of this graph.
            include_start: If True, yield the start_node first.

        Yields:
            T: Each reached node.
        """
        visited: set[T] = {start_node}

        if include_start:
            if not limit_to_graph or start_node in self._nodes:
                yield start_node

        def discover(current: T) -> Iterator[T]:
            neighbors = (
                current.dependents
                if direction == Direction.DOWN
                else current.depends_on
            )
            for neighbor in neighbors:
                if neighbor not in visited:
                    if limit_to_graph and neighbor not in self._nodes:
                        continue
                    visited.add(neighbor)
                    yield neighbor
                    yield from discover(neighbor)

        yield from discover(start_node)

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

    @staticmethod
    def parse(
        parser_fnc: Callable[..., Graph[Any]], source: str | Path, **kwargs: Any
    ) -> Graph[Any]:
        """
        Parse a graph from a source using a parser function.

        Args:
            parser_fnc: The parser function to use (e.g., load_graph_json).
            source: The source to parse (string or path).
            **kwargs: Additional arguments passed to the parser function.

        Returns:
            Graph: A new Graph instance.
        """
        return parser_fnc(source, **kwargs)

    @classmethod
    def from_csv(cls, source: str | Path, **kwargs: Any) -> Graph[Any]:
        """Create a Graph from a CSV edge list."""
        from .parsers.csv import load_graph_csv

        return cls.parse(load_graph_csv, source, **kwargs)

    @classmethod
    def from_graphml(cls, source: str | Path, **kwargs: Any) -> Graph[Any]:
        """Create a Graph from a GraphML file or string."""
        from .parsers.graphml import load_graph_graphml

        return cls.parse(load_graph_graphml, source, **kwargs)

    @classmethod
    def from_json(cls, source: str | Path, **kwargs: Any) -> Graph[Any]:
        """Create a Graph from a JSON file or string."""
        from .parsers.json import load_graph_json

        return cls.parse(load_graph_json, source, **kwargs)

    @classmethod
    def from_toml(cls, source: str | Path, **kwargs: Any) -> Graph[Any]:
        """Create a Graph from a TOML file or string."""
        from .parsers.toml import load_graph_toml

        return cls.parse(load_graph_toml, source, **kwargs)

    @classmethod
    def from_yaml(cls, source: str | Path, **kwargs: Any) -> Graph[Any]:
        """Create a Graph from a YAML file or string."""
        from .parsers.yaml import load_graph_yaml

        return cls.parse(load_graph_yaml, source, **kwargs)

    def subgraph_filtered(self, fn: Callable[[T], bool]) -> Graph[T]:
        """
        Create a new subgraph containing only nodes that satisfy the predicate.

        Args:
            fn (Callable[[T], bool]): The predicate function.

        Returns:
            Graph[T]: A new Graph containing the filtered nodes.
        """
        logger.debug("Creating filtered subgraph.")
        return Graph([node for node in self._nodes if fn(node)], discover=True)

    def subgraph_tagged(self, tag: str) -> Graph[T]:
        """
        Create a new subgraph containing only nodes with the specified tag.

        Args:
            tag (str): The tag to filter by.

        Returns:
            Graph[T]: A new Graph containing the tagged nodes.
        """
        logger.debug(f"Creating subgraph for tag: {tag}")
        return Graph(
            [node for node in self._nodes if node.is_tagged(tag)], discover=True
        )

    def upstream_of(self, node: T) -> Graph[T]:
        """
        Create a new graph containing the given node and all its ancestors.

        Args:
            node (T): The node to start from.

        Returns:
            Graph[T]: A new Graph instance.
        """
        if node not in self._nodes:
            raise KeyError(f"Node '{node.reference}' not found in graph.")

        nodes = {node} | set(self.ancestors(node))
        return Graph(nodes)

    def downstream_of(self, node: T) -> Graph[T]:
        """
        Create a new graph containing the given node and all its descendants.

        Args:
            node (T): The node to start from.

        Returns:
            Graph[T]: A new Graph instance.
        """
        if node not in self._nodes:
            raise KeyError(f"Node '{node.reference}' not found in graph.")

        nodes = {node} | set(self.descendants(node))
        return Graph(nodes)

    def cpm_analysis(self) -> dict[T, dict[str, float]]:
        """
        Perform Critical Path Method (CPM) analysis on the graph.
        Assumes all nodes have a 'duration' attribute.

        Returns:
            dict[T, dict[str, float]]: A dictionary mapping each node to its CPM values:
                - 'ES': Earliest Start
                - 'EF': Earliest Finish
                - 'LS': Latest Start
                - 'LF': Latest Finish
                - 'slack': Total Slack (LF - EF)
        """
        logger.debug("Starting CPM analysis.")
        topo_order = self.topological_order()
        if not topo_order:
            return {}

        analysis: dict[T, dict[str, float]] = {
            node: {"ES": 0.0, "EF": 0.0, "LS": 0.0, "LF": 0.0, "slack": 0.0}
            for node in topo_order
        }

        # 1. Forward Pass (ES, EF)
        for node in topo_order:
            max_ef = 0.0
            for dep in node.depends_on:
                if dep in analysis:
                    max_ef = max(max_ef, analysis[dep]["EF"])
            analysis[node]["ES"] = max_ef
            analysis[node]["EF"] = max_ef + node.duration

        # 2. Backward Pass (LF, LS)
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
        """
        Identify the nodes on the critical path (slack == 0).

        Returns:
            list[T]: A list of nodes on the critical path, in topological order.
        """
        analysis = self.cpm_analysis()
        return [
            node
            for node in self.topological_order()
            if abs(analysis[node]["slack"]) < 1e-9
        ]

    def longest_path(self) -> list[T]:
        """
        Find the longest path in the graph based on node durations.
        In a DAG, this is equivalent to the critical path chain.

        Returns:
            list[T]: The nodes forming the longest path.
        """
        # This is a bit more complex than just critical_path() if there are multiple critical paths.
        # But for dependency graphs, any path where slack == 0 is "a" longest path.
        # To get a specific chain:
        analysis = self.cpm_analysis()
        cp_nodes = {
            node for node, vals in analysis.items() if abs(vals["slack"]) < 1e-9
        }

        if not cp_nodes:
            return []

        # Find a source on critical path
        current = None
        for node in self.sources:
            if node in cp_nodes:
                current = node
                break

        if current is None:
            # Fallback: just take the first CP node in topo order
            current = sorted(
                list(cp_nodes), key=lambda n: self.topological_order().index(n)
            )[0]

        path = [current]
        while True:
            next_node = None
            # Find a dependent that is also on critical path and continues the timing
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

    def all_paths(self, source: T, target: T) -> list[list[T]]:
        """
        Find all possible paths between two nodes.

        Args:
            source (T): Starting node.
            target (T): Ending node.

        Returns:
            list[list[T]]: A list of all paths, where each path is a list of nodes.
        """

        def find_all_paths(current: T, goal: T, path: list[T]) -> list[list[T]]:
            path = path + [current]
            if current == goal:
                return [path]
            paths = []
            for neighbor in current.dependents:
                if neighbor in self._nodes:
                    new_paths = find_all_paths(neighbor, goal, path)
                    for p in new_paths:
                        paths.append(p)
            return paths

        return find_all_paths(source, target, [])

    def diff(self, other: Graph[T]) -> dict[str, Any]:
        """
        Compare this graph with another graph.

        Returns:
            dict[str, Any]: A dictionary containing differences:
                - 'added_nodes': references of nodes in other but not in self.
                - 'removed_nodes': references of nodes in self but not in other.
                - 'modified_nodes': references of nodes in both but with different properties.
                - 'added_edges': (u, v) tuples of edges in other but not in self.
                - 'removed_edges': (u, v) tuples of edges in self but not in other.
                - 'modified_edges': (u, v) tuples of edges in both but with different attributes.
        """
        self_refs = {node.reference for node in self._nodes}
        other_refs = {node.reference for node in other._nodes}

        added_nodes = other_refs - self_refs
        removed_nodes = self_refs - other_refs

        modified_nodes = set()
        for ref in self_refs & other_refs:
            n1 = self[ref]
            n2 = other[ref]
            if (
                n1.tags != n2.tags
                or n1.duration != n2.duration
                or n1.status != n2.status
            ):
                modified_nodes.add(ref)

        def get_edges(g: Graph[T]):
            edges = {}
            for u in g._nodes:
                for v in u.dependents:
                    if v in g._nodes:
                        edges[(u.reference, v.reference)] = u.edge_attributes(v)
            return edges

        self_edges = get_edges(self)
        other_edges = get_edges(other)

        self_edge_set = set(self_edges.keys())
        other_edge_set = set(other_edges.keys())

        added_edges = other_edge_set - self_edge_set
        removed_edges = self_edge_set - other_edge_set
        modified_edges = set()

        for edge in self_edge_set & other_edge_set:
            if self_edges[edge] != other_edges[edge]:
                modified_edges.add(edge)

        return {
            "added_nodes": added_nodes,
            "removed_nodes": removed_nodes,
            "modified_nodes": modified_nodes,
            "added_edges": added_edges,
            "removed_edges": removed_edges,
            "modified_edges": modified_edges,
        }

    def topological_order(self) -> list[T]:
        """
        Get the nodes in topological order.
        Only nodes that are members of this graph are included.

        Returns:
            list[T]: A list of member nodes sorted topologically.
        """
        if self._topological_order is None:
            logger.debug("Calculating topological order.")
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            # Filter the static order to only include nodes that are in this graph
            self._topological_order = [
                node for node in sorter.static_order() if node in self._nodes
            ]

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
            new_node._dependents = {}
            new_node._depends_on = {}
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
                    # Preserve edge attributes
                    attrs = u.edge_attributes(v)
                    new_graph.add_edge(node_map[u], node_map[v], **attrs)

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
        embed_checksum: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Export the graph using an export function.

        Args:
            export_fnc: The export function to use (e.g., export_topology_graphviz_svg).
            output: The output file path.
            transitive_reduction: If True, export the transitive reduction of the graph.
            embed_checksum: If True, embed the graph's checksum as a comment at the top.
            **kwargs: Additional arguments passed to the export function.
        """
        from pathlib import Path

        from .registry import CREATOR_MAP
        from .views.utils import wrap_with_checksum

        p = Path(output)
        target = self.transitive_reduction() if transitive_reduction else self

        if not embed_checksum:
            return export_fnc(target, p, **kwargs)

        # To embed checksum, we need to capture the output string first.
        create_fnc = CREATOR_MAP.get(export_fnc)

        if not create_fnc:
            # Fallback: export normally if we can't find a string-generating version
            export_name = getattr(export_fnc, "__name__", str(export_fnc))
            logger.warning(
                f"Could not find string-generating version of {export_name}. Exporting normally without checksum embedding."
            )
            return export_fnc(target, p, **kwargs)

        content = create_fnc(target, **kwargs)
        checksum = target.checksum()
        wrapped = wrap_with_checksum(content, checksum, p.suffix)

        with open(p, "w+") as f:
            f.write(wrapped)
