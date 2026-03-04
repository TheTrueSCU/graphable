from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable
from ..registry import register_view

logger = getLogger(__name__)


@dataclass
class YamlStylingConfig:
    """
    Configuration for YAML graph serialization.

    Attributes:
        node_data_fnc: Optional function to add extra data to each node's YAML object.
        reference_fnc: Function to generate the string identifier for each node.
        indent: YAML indentation level.
    """

    node_data_fnc: Callable[[Graphable[Any]], dict[str, Any]] | None = None
    reference_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    indent: int = 2


def create_topology_yaml(graph: Graph, config: YamlStylingConfig | None = None) -> str:
    """
    Generate a YAML representation of the graph.
    Requires 'PyYAML' to be installed.

    Args:
        graph (Graph): The graph to convert.
        config (YamlStylingConfig | None): Serialization configuration.

    Returns:
        str: A YAML string containing 'nodes' and 'edges'.
    """
    try:
        from yaml import dump
    except ImportError:
        logger.error("PyYAML not found. Please install it with 'pip install PyYAML'.")
        raise ImportError(
            "PyYAML is required for YAML export. Install it with 'pip install PyYAML'."
        )

    logger.debug("Creating YAML representation of the graph.")
    config = config or YamlStylingConfig()

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

    return dump(data, indent=config.indent, sort_keys=False)


@register_view([".yaml", ".yml"], creator_fnc=create_topology_yaml)
def export_topology_yaml(
    graph: Graph,
    output: Path,
    config: YamlStylingConfig | None = None,
) -> None:
    """
    Export the graph to a YAML file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (YamlStylingConfig | None): Serialization configuration.
    """
    logger.info(f"Exporting YAML to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_yaml(graph, config))
