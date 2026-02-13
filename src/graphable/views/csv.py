import csv
import io
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable
from ..registry import register_view

logger = getLogger(__name__)


def create_topology_csv(
    graph: Graph,
    node_text_fnc: Callable[[Graphable[Any]], str] = lambda n: n.reference,
    include_header: bool = True,
) -> str:
    """
    Generate a CSV edge list from a Graph.

    Args:
        graph (Graph): The graph to convert.
        node_text_fnc: Function to generate the text for each node.
        include_header: Whether to include a header row ('source','target').

    Returns:
        str: The CSV edge list as a string.
    """
    logger.debug("Creating CSV edge list.")
    output = io.StringIO()
    writer = csv.writer(output)

    if include_header:
        writer.writerow(["source", "target"])

    for node in graph.topological_order():
        source_text = node_text_fnc(node)
        for dependent, _ in graph.internal_dependents(node):
            target_text = node_text_fnc(dependent)
            writer.writerow([source_text, target_text])

    return output.getvalue()


@register_view(".csv", creator_fnc=create_topology_csv)
def export_topology_csv(
    graph: Graph,
    output: Path,
    node_text_fnc: Callable[[Graphable[Any]], str] = lambda n: n.reference,
    include_header: bool = True,
) -> None:
    """
    Export the graph to a CSV file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        node_text_fnc: Function to generate the text for each node.
        include_header: Whether to include a header row.
    """
    logger.info(f"Exporting CSV edge list to: {output}")
    with open(output, "w+", newline="") as f:
        f.write(create_topology_csv(graph, node_text_fnc, include_header))
