import xml.etree.ElementTree as ET
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable
from xml.dom import minidom

from ..graph import Graph
from ..graphable import Graphable

logger = getLogger(__name__)


@dataclass
class GraphmlStylingConfig:
    """
    Configuration for GraphML serialization.

    Attributes:
        node_ref_fnc: Function to generate the unique ID for each node.
        attr_mapping: Dictionary mapping Graphable attributes to GraphML data keys.
    """

    node_ref_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    # We could extend this to support more complex data mapping if needed.


def create_topology_graphml(
    graph: Graph, config: GraphmlStylingConfig | None = None
) -> str:
    """
    Generate a GraphML (XML) representation of the graph.

    Args:
        graph (Graph): The graph to convert.
        config (GraphmlStylingConfig | None): Export configuration.

    Returns:
        str: The GraphML XML string.
    """
    logger.debug("Creating GraphML representation.")
    config = config or GraphmlStylingConfig()

    # Create root element
    root = ET.Element(
        "graphml",
        {
            "xmlns": "http://graphml.graphdrawing.org/xmlns",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd",
        },
    )

    # Define attributes (keys)
    # 1. Tags
    ET.SubElement(
        root,
        "key",
        {
            "id": "tags",
            "for": "node",
            "attr.name": "tags",
            "attr.type": "string",
        },
    )

    # Create graph element
    graph_elem = ET.SubElement(root, "graph", {"id": "G", "edgedefault": "directed"})

    # Nodes
    for node in graph.topological_order():
        node_id = config.node_ref_fnc(node)
        node_elem = ET.SubElement(graph_elem, "node", {"id": node_id})

        # Add tags as data
        if node.tags:
            data_elem = ET.SubElement(node_elem, "data", {"key": "tags"})
            data_elem.text = ",".join(node.tags)

        # Edges
        for dependent in node.dependents:
            dep_id = config.node_ref_fnc(dependent)
            ET.SubElement(
                graph_elem,
                "edge",
                {
                    "id": f"e_{node_id}_{dep_id}",
                    "source": node_id,
                    "target": dep_id,
                },
            )

    # Pretty print XML
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(xml_str)
    return parsed_xml.toprettyxml(indent="  ")


def export_topology_graphml(
    graph: Graph, output: Path, config: GraphmlStylingConfig | None = None
) -> None:
    """
    Export the graph to a GraphML (.graphml) file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (GraphmlStylingConfig | None): Export configuration.
    """
    logger.info(f"Exporting GraphML to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_graphml(graph, config))
