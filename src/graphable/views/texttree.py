from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable

logger = getLogger(__name__)


@dataclass
class TextTreeStylingConfig:
    """
    Configuration for text tree representation of the graph.

    Attributes:
        initial_indent: String to use for initial indentation.
        node_text_fnc: Function to generate the text representation of a node.
    """

    initial_indent: str = ""
    node_text_fnc: Callable[[Graphable[Any]], str] = lambda n: n.reference


def create_topology_tree_txt(
    graph: Graph, config: TextTreeStylingConfig | None = None
) -> str:
    """
    Create a text-based tree representation of the graph topology.

    Args:
        graph (Graph): The graph to convert.
        config (TextTreeStylingConfig | None): Styling configuration.

    Returns:
        str: The text tree representation.
    """
    if config is None:
        config = TextTreeStylingConfig()

    logger.debug("Creating topology tree text.")

    def create_topology_subtree_txt(
        node: Graphable[Any],
        indent: str = "",
        is_last: bool = True,
        is_root: bool = True,
        visited: set[Graphable[Any]] | None = None,
    ) -> str:
        """
        Recursively generate the text representation for a subtree.

        Args:
            node (Graphable): The current node being processed.
            indent (str): The current indentation string.
            is_last (bool): Whether this node is the last sibling.
            is_root (bool): Whether this is the root of the (sub)tree.
            visited (set[Graphable] | None): Set of already visited nodes to detect cycles/redundancy.

        Returns:
            str: The text representation of the subtree.
        """
        if visited is None:
            visited = set[Graphable]()
        already_seen: bool = node in visited

        subtree: list[str] = []
        if is_root:
            subtree.append(f"{indent}{config.node_text_fnc(node)}")

            next_indent: str = indent

        else:
            marker: str = "└─ " if is_last else "├─ "
            suffix: str = " (see above)" if already_seen and node.depends_on else ""
            subtree.append(f"{indent}{marker}{config.node_text_fnc(node)}{suffix}")

            next_indent: str = indent + ("   " if is_last else "│  ")

        if already_seen:
            return "\n".join(subtree)
        visited.add(node)

        for i, subnode in enumerate(node.depends_on, start=1):
            subtree.append(
                create_topology_subtree_txt(
                    node=subnode,
                    indent=next_indent,
                    is_last=(i == len(node.depends_on)),
                    is_root=False,
                    visited=visited,
                )
            )

        return "\n".join(subtree)

    tree: list[str] = []
    for node in graph.sinks:
        tree.append(
            create_topology_subtree_txt(
                node=node, indent=config.initial_indent, is_root=True
            )
        )
    return "\n".join(tree)


def export_topology_tree_txt(
    graph: Graph, output: Path, config: TextTreeStylingConfig | None = None
) -> None:
    """
    Export the graph to a text tree file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (TextTreeStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting topology tree text to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_tree_txt(graph, config))
