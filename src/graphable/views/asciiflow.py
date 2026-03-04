from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable
from ..registry import register_view

logger = getLogger(__name__)


@dataclass
class AsciiflowStylingConfig:
    """
    Configuration for ASCII flowchart representation of the graph.

    Attributes:
        node_text_fnc: Function to generate the text representation of a node.
        show_tags: Whether to include tags in the output.
    """

    node_text_fnc: Callable[[Graphable[Any]], str] = lambda n: n.reference
    show_tags: bool = False


def create_topology_ascii_flow(
    graph: Graph, config: AsciiflowStylingConfig | None = None
) -> str:
    """
    Create an ASCII-based flowchart representation of the graph.
    Unlike TextTree, this explicitly shows multiple parents by listing connections.

    Args:
        graph (Graph): The graph to convert.
        config (AsciiflowStylingConfig | None): Styling configuration.

    Returns:
        str: The ASCII flowchart representation.
    """
    if config is None:
        config = AsciiflowStylingConfig()

    logger.debug("Creating ASCII flowchart text.")

    lines: list[str] = []

    # We'll group by "levels" using topological order to give a sense of flow
    nodes = graph.topological_order()

    for node in nodes:
        node_text = config.node_text_fnc(node)
        tags_info = (
            f" [{', '.join(node.tags)}]" if config.show_tags and node.tags else ""
        )

        # Box the node
        box_width = len(node_text + tags_info) + 2
        top_border = "+" + "-" * box_width + "+"
        middle = f"| {node_text}{tags_info} |"

        lines.append(top_border)
        lines.append(middle)
        lines.append(top_border)

        # Show dependencies (outgoing edges)
        internal_deps = list(graph.internal_dependents(node))
        if internal_deps:
            for i, (dependent, _) in enumerate(internal_deps):
                dep_text = config.node_text_fnc(dependent)
                if i == 0:
                    lines.append(f"  v\n  +--> {dep_text}")
                else:
                    lines.append(f"  +--> {dep_text}")

        lines.append("")  # Spacer between nodes

    return "\n".join(lines)


@register_view(".ascii", creator_fnc=create_topology_ascii_flow)
def export_topology_ascii_flow(
    graph: Graph, output: Path, config: AsciiflowStylingConfig | None = None
) -> None:
    """
    Export the graph to an ASCII flowchart file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (AsciiFlowStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting ASCII flowchart to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_ascii_flow(graph, config))
