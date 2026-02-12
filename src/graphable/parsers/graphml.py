import xml.etree.ElementTree as ET
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..graphable import Graphable
from .utils import is_path

logger = getLogger(__name__)


def load_graph_graphml(
    source: str | Path, reference_type: type = str
) -> Graph[Graphable[Any]]:
    """
    Load a graph from a GraphML file or string.

    Args:
        source: Path to a GraphML file or GraphML string.
        reference_type: The type to cast the node reference to (default: str).

    Returns:
        Graph: A new Graph instance populated from the GraphML data.
    """
    if is_path(source):
        logger.debug(f"Loading GraphML from file: {source}")
        tree = ET.parse(source)
        root = tree.getroot()
    else:
        logger.debug("Loading GraphML from string.")
        root = ET.fromstring(str(source))

    # GraphML namespaces can be tricky, but often it's just http://graphml.graphdrawing.org/xmlns
    ns = {"ns": "http://graphml.graphdrawing.org/xmlns"}

    # If the root doesn't match the namespace, try without it
    if "http://graphml.graphdrawing.org/xmlns" not in root.tag:
        ns = {}

    graph_elem = root.find(".//ns:graph", ns) if ns else root.find(".//graph")
    if graph_elem is None:
        logger.error("No <graph> element found in GraphML.")
        return Graph()

    node_map: dict[str, Graphable[Any]] = {}
    g = Graph()

    # Find nodes
    nodes = graph_elem.findall("ns:node", ns) if ns else graph_elem.findall("node")
    for node_elem in nodes:
        node_id = node_elem.get("id")
        if not node_id:
            continue

        # Look for tags or reference in data elements
        reference = node_id
        tags = []

        data_elems = (
            node_elem.findall("ns:data", ns) if ns else node_elem.findall("data")
        )
        for data in data_elems:
            key = data.get("key")
            if key == "reference":
                reference = data.text or node_id
            elif key == "tags":
                if data.text:
                    tags = [t.strip() for t in data.text.split(",") if t.strip()]

        try:
            typed_ref = reference_type(reference)
        except (ValueError, TypeError):
            typed_ref = reference

        node = Graphable(typed_ref)
        for tag in tags:
            node.add_tag(tag)

        node_map[node_id] = node

    # Find edges
    edges = graph_elem.findall("ns:edge", ns) if ns else graph_elem.findall("edge")
    for edge_elem in edges:
        u_id = edge_elem.get("source")
        v_id = edge_elem.get("target")

        if u_id in node_map and v_id in node_map:
            g.add_edge(node_map[u_id], node_map[v_id])

    # Add any orphans
    for node in node_map.values():
        if node not in g:
            g.add_node(node)

    logger.info(f"Loaded graph with {len(g)} nodes from GraphML.")
    return g
