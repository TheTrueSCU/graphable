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
class CytoscapeStylingConfig:
    """
    Configuration for Cytoscape.js JSON serialization.

    Attributes:
        node_data_fnc: Optional function to add extra data to each node's 'data' object.
        edge_data_fnc: Optional function to add extra data to each edge's 'data' object.
        reference_fnc: Function to generate the string identifier for each node.
        indent: JSON indentation level.
    """

    node_data_fnc: Callable[[Graphable[Any]], dict[str, Any]] | None = None
    edge_data_fnc: Callable[[Graphable[Any], Graphable[Any]], dict[str, Any]] | None = (
        None
    )
    reference_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    indent: int | str | None = 2


def create_topology_cytoscape(
    graph: Graph, config: CytoscapeStylingConfig | None = None
) -> str:
    """
    Generate a Cytoscape.js compatible JSON representation of the graph.

    Args:
        graph (Graph): The graph to convert.
        config (CytoscapeStylingConfig | None): Serialization configuration.

    Returns:
        str: A JSON string in Cytoscape.js elements format.
    """
    logger.debug("Creating Cytoscape JSON representation.")
    config = config or CytoscapeStylingConfig()

    elements = []

    for node in graph.topological_order():
        # Node
        node_id = config.reference_fnc(node)
        node_data = {
            "id": node_id,
            "label": str(node.reference),
            "tags": list(node.tags),
        }
        if config.node_data_fnc:
            node_data.update(config.node_data_fnc(node))

        elements.append({"data": node_data})

        # Edges
        for dependent, attrs in graph.internal_dependents(node):
            dep_id = config.reference_fnc(dependent)
            edge_id = f"{node_id}_{dep_id}"
            edge_data = {
                "id": edge_id,
                "source": node_id,
                "target": dep_id,
            }
            if config.edge_data_fnc:
                edge_data.update(config.edge_data_fnc(node, dependent))

            # Add existing attributes
            edge_data.update(attrs)

            elements.append({"data": edge_data})

    return json.dumps(elements, indent=config.indent)


@register_view(".cy.json", creator_fnc=create_topology_cytoscape)
def export_topology_cytoscape(
    graph: Graph,
    output: Path,
    config: CytoscapeStylingConfig | None = None,
) -> None:
    """
    Export the graph to a Cytoscape JSON file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (CytoscapeStylingConfig | None): Serialization configuration.
    """
    logger.info(f"Exporting Cytoscape JSON to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_cytoscape(graph, config))
