from __future__ import annotations

from graphlib import CycleError, TopologicalSorter
from hashlib import blake2b
from logging import getLogger
from pathlib import Path
from typing import Any, Callable, Iterator

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
    g = Graph(set(contains))
    g.discover()
    logger.info(f"Graph built with {len(g)} total nodes.")
    return g


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
        self._nodes: set[T] = set()
        self._topological_order: list[T] | None = None
        self._parallel_topological_order: list[set[T]] | None = None
        self._checksum: str | None = None

        if initial:
            for node in initial:
                self.add_node(node)
            self.check_consistency()
            self.check_cycles()

    def discover(self) -> None:
        """
        Traverse the entire connectivity of the current nodes and add any
        reachable ancestors or descendants that are not yet members.
        """
        logger.debug(f"Discovering reachable nodes from {len(self._nodes)} base nodes.")

        def go_down(node: T, nodes: set[T]) -> None:
            for down_node in node.dependents:
                if down_node in nodes:
                    continue

                nodes.add(down_node)
                go_down(down_node, nodes)

        def go_up(node: T, nodes: set[T]) -> None:
            for up_node in node.depends_on:
                if up_node in nodes:
                    continue

                nodes.add(up_node)
                go_up(up_node, nodes)

        new_nodes: set[T] = set(self._nodes)
        for node in list(self._nodes):
            go_up(node, new_nodes)
            go_down(node, new_nodes)

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
        The checksum accounts for all member nodes (references and tags)
        and edges between them. External nodes are excluded.

        Returns:
            str: The hexadecimal digest of the graph.
        """
        if self._checksum is not None:
            return self._checksum

        # 1. Sort nodes by reference to ensure deterministic iteration
        sorted_nodes = sorted(self._nodes, key=lambda n: str(n.reference))

        hasher = blake2b()

        for node in sorted_nodes:
            # 2. Add node reference
            hasher.update(str(node.reference).encode())

            # 3. Add sorted tags
            for tag in sorted(node.tags):
                hasher.update(f":tag:{tag}".encode())

            # 4. Add sorted dependents (edges) - Only those in the graph
            internal_dependents = [d for d in node.dependents if d in self._nodes]
            for dep in sorted(internal_dependents, key=lambda n: str(n.reference)):
                hasher.update(f":edge:{dep.reference}".encode())

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

        p = Path(path)
        ext = p.suffix.lower()
        match ext:
            case ".json":
                g = cls.from_json(p, **kwargs)
            case ".yaml" | ".yml":
                g = cls.from_yaml(p, **kwargs)
            case ".toml":
                g = cls.from_toml(p, **kwargs)
            case ".csv":
                g = cls.from_csv(p, **kwargs)
            case ".graphml":
                g = cls.from_graphml(p, **kwargs)
            case _:
                raise ValueError(f"Unsupported extension for reading: {ext}")

        if embedded := extract_checksum(p):
            if not g.validate_checksum(embedded):
                raise ValueError(f"Checksum validation failed for {p}")
        return g

    def write(
        self,
        path: Path | str,
        transitive_reduction: bool = False,
        embed_checksum: bool = False,
        **kwargs: Any,
    ) -> None:
        """Write the graph to a file, automatically detecting the format."""
        p = Path(path)
        ext = p.suffix.lower()
        match ext:
            case ".json":
                from .views.json import export_topology_json as fnc
            case ".yaml" | ".yml":
                from .views.yaml import export_topology_yaml as fnc
            case ".toml":
                from .views.toml import export_topology_toml as fnc
            case ".csv":
                from .views.csv import export_topology_csv as fnc
            case ".graphml":
                from .views.graphml import export_topology_graphml as fnc
            case ".dot" | ".gv":
                from .views.graphviz import export_topology_graphviz_dot as fnc
            case ".mmd":
                from .views.mermaid import export_topology_mermaid_mmd as fnc
            case ".d2":
                from .views.d2 import export_topology_d2 as fnc
            case ".puml":
                from .views.plantuml import export_topology_plantuml as fnc
            case ".html":
                from .views.html import export_topology_html as fnc
            case ".tex":
                from .views.tikz import export_topology_tikz as fnc
            case ".txt":
                from .views.texttree import export_topology_tree_txt as fnc
            case ".ascii":
                from .views.asciiflow import export_topology_ascii_flow as fnc
            case ".svg":
                from .views.mermaid import export_topology_mermaid_svg as fnc
            case _:
                raise ValueError(f"Unsupported extension: {ext}")
        return self.export(fnc, p, transitive_reduction, embed_checksum, **kwargs)

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

        def discover(current: T, visited: set[T]) -> Iterator[T]:
            for dep in current.depends_on:
                if dep not in visited:
                    visited.add(dep)
                    yield dep
                    yield from discover(dep, visited)

        return discover(node, set())

    def descendants(self, node: T) -> Iterator[T]:
        """
        Get an iterator for all nodes that depend on the given node, recursively.

        Args:
            node (T): The starting node.

        Yields:
            T: The next descendant node.
        """

        def discover(current: T, visited: set[T]) -> Iterator[T]:
            for sub in current.dependents:
                if sub not in visited:
                    visited.add(sub)
                    yield sub
                    yield from discover(sub, visited)

        return discover(node, set())

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

        from .views.utils import wrap_with_checksum

        p = Path(output)
        target = self.transitive_reduction() if transitive_reduction else self

        if not embed_checksum:
            return export_fnc(target, p, **kwargs)

        # To embed checksum, we need to capture the output string first.
        # Most of our 'export_*' functions are just wrappers around 'create_*'.
        # We'll look for the corresponding create function.
        import types

        if isinstance(export_fnc, types.FunctionType):
            fnc_name = export_fnc.__name__.replace("export_", "create_")
        else:
            # Fallback for other callables
            logger.warning(
                f"Callable {export_fnc} is not a function. Exporting normally."
            )
            return export_fnc(target, p, **kwargs)

        import importlib

        module_path = export_fnc.__module__
        module = importlib.import_module(module_path)
        create_fnc = getattr(module, fnc_name, None)

        if not create_fnc:
            # Fallback: if we can't find create_*, just export normally without embedding
            logger.warning(
                f"Could not find {fnc_name} to embed checksum. Exporting normally."
            )
            return export_fnc(target, p, **kwargs)

        content = create_fnc(target, **kwargs)
        checksum = target.checksum()
        wrapped = wrap_with_checksum(content, checksum, p.suffix)

        with open(p, "w+") as f:
            f.write(wrapped)
