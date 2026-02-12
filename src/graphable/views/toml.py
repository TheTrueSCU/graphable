from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable

logger = getLogger(__name__)


@dataclass
class TomlStylingConfig:
    """
    Configuration for TOML graph serialization.

    Attributes:
        node_data_fnc: Optional function to add extra data to each node's TOML object.
        reference_fnc: Function to generate the string identifier for each node.
    """

    node_data_fnc: Callable[[Graphable[Any]], dict[str, Any]] | None = None
    reference_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)


def create_topology_toml(graph: Graph, config: TomlStylingConfig | None = None) -> str:
    """
    Generate a TOML representation of the graph.
    Requires 'tomli-w' to be installed.

    Args:
        graph (Graph): The graph to convert.
        config (TomlStylingConfig | None): Serialization configuration.

    Returns:
        str: A TOML string containing 'nodes' and 'edges'.
    """
    try:
        import tomli_w
    except ImportError:
        logger.error("tomli-w not found. Please install it with 'pip install tomli-w'.")
        raise ImportError(
            "tomli-w is required for TOML export. Install it with 'pip install tomli-w'."
        )

    logger.debug("Creating TOML representation of the graph.")
    config = config or TomlStylingConfig()

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

        for dependent in node.dependents:
            edges.append({"source": node_id, "target": config.reference_fnc(dependent)})

    data = {"nodes": nodes, "edges": edges}

    return tomli_w.dumps(data)


def export_topology_toml(
    graph: Graph,
    output: Path,
    config: TomlStylingConfig | None = None,
) -> None:
    """
    Export the graph to a TOML file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (TomlStylingConfig | None): Serialization configuration.
    """
    logger.info(f"Exporting TOML to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_toml(graph, config))
