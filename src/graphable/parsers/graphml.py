import xml.etree.ElementTree as ET
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..registry import register_parser
from .utils import build_graph_from_data, is_path

logger = getLogger(__name__)


@register_parser(".graphml")
def load_graph_graphml(source: str | Path, reference_type: type = str) -> Graph[Any]:
    """
    Load a Graph from a GraphML XML source.

    Args:
        source: GraphML XML string or path to a GraphML file.
        reference_type: The type to cast the reference string to.

    Returns:
        Graph: The loaded Graph instance.
    """
    if is_path(source):
        tree = ET.parse(source)
        root = tree.getroot()
    else:
        root = ET.fromstring(str(source))

    # GraphML uses namespaces
    ns = {"g": "http://graphml.graphdrawing.org/xmlns"}

    graph_elem = root.find("g:graph", ns)
    if graph_elem is None:
        # Fallback for no namespace
        graph_elem = root.find("graph")
        if graph_elem is None:
            return Graph()
        ns = {}

    nodes_data = []
    for node_elem in graph_elem.findall("g:node" if ns else "node", ns):
        node_id = node_elem.get("id")
        node_entry = {"id": node_id}

        # Handle data fields (tags, etc)
        for data_elem in node_elem.findall("g:data" if ns else "data", ns):
            key = data_elem.get("key")
            if key == "tags" and data_elem.text:
                node_entry["tags"] = data_elem.text.split(",")
            elif key == "duration" and data_elem.text:
                node_entry["duration"] = data_elem.text
            elif key == "status" and data_elem.text:
                node_entry["status"] = data_elem.text

        nodes_data.append(node_entry)

    edges_data = []
    for edge_elem in graph_elem.findall("g:edge" if ns else "edge", ns):
        u_id = edge_elem.get("source")
        v_id = edge_elem.get("target")
        edge_entry = {"source": u_id, "target": v_id}

        # Handle edge attributes
        for data_elem in edge_elem.findall("g:data" if ns else "data", ns):
            key = data_elem.get("key")
            if key and data_elem.text:
                edge_entry[key] = data_elem.text

        edges_data.append(edge_entry)

    g = build_graph_from_data(nodes_data, edges_data, reference_type)
    logger.info(f"Loaded graph with {len(g)} nodes from GraphML.")
    return g
