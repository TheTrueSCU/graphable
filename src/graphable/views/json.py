import json
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable
from ..registry import register_view

logger = getLogger(__name__)


@dataclass
class JsonStylingConfig:
    """
    Configuration for JSON graph serialization.

    Attributes:
        node_data_fnc: Optional function to add extra data to each node's JSON object.
        reference_fnc: Function to generate the string identifier for each node.
        indent: JSON indentation level.
    """

    node_data_fnc: Callable[[Graphable[Any]], dict[str, Any]] | None = None
    reference_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    indent: int | str | None = 2


def create_topology_json(graph: Graph, config: JsonStylingConfig | None = None) -> str:
    """
    Generate a JSON representation of the graph.

    Args:
        graph (Graph): The graph to convert.
        config (JsonStylingConfig | None): Serialization configuration.

    Returns:
        str: A JSON string containing 'nodes' and 'edges'.
    """
    logger.debug("Creating JSON representation of the graph.")
    config = config or JsonStylingConfig()

    nodes = []
    edges = []

    for node in graph.topological_order():
        node_id = config.reference_fnc(node)
        node_entry = {
            "id": node_id,
            "reference": str(node.reference),
            "tags": list(node.tags),
        }
        if config.node_data_fnc:
            node_entry.update(config.node_data_fnc(node))
        nodes.append(node_entry)

        for dependent, _ in graph.internal_dependents(node):
            edges.append({"source": node_id, "target": config.reference_fnc(dependent)})

    data = {"nodes": nodes, "edges": edges}

    return json.dumps(data, indent=config.indent)


@register_view(".json", creator_fnc=create_topology_json)
def export_topology_json(
    graph: Graph,
    output: Path,
    config: JsonStylingConfig | None = None,
) -> None:
    """
    Export the graph to a JSON file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (JSONStylingConfig | None): Serialization configuration.
    """
    logger.info(f"Exporting JSON to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_json(graph, config))
