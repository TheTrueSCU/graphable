import json
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..graphable import Graphable
from .utils import is_path

logger = getLogger(__name__)


def load_graph_json(
    source: str | Path, reference_type: type = str
) -> Graph[Graphable[Any]]:
    """
    Load a graph from a JSON string or file.

    Args:
        source: JSON string or path to a JSON file.
        reference_type: The type to cast the node reference to (default: str).

    Returns:
        Graph: A new Graph instance populated from the JSON data.
    """
    if is_path(source):
        logger.debug(f"Loading JSON from file: {source}")
        with open(source, "r") as f:
            data = json.load(f)
    else:
        logger.debug("Loading JSON from string.")
        data = json.loads(str(source))

    # Handle wrapped structure: {"checksum": "...", "graph": {"nodes": ..., "edges": ...}}
    if "graph" in data and ("nodes" not in data or "edges" not in data):
        logger.debug("Detected wrapped JSON structure, extracting 'graph' object.")
        data = data["graph"]

    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])

    # 1. Create all nodes
    node_map: dict[str, Graphable[Any]] = {}
    for entry in nodes_data:
        node_id = entry["id"]
        reference = entry.get("reference", node_id)

        # Cast reference if needed
        try:
            typed_reference = reference_type(reference)
        except (ValueError, TypeError):
            typed_reference = reference

        node = Graphable(typed_reference)
        for tag in entry.get("tags", []):
            node.add_tag(tag)

        node_map[node_id] = node

    # 2. Link nodes with edges
    g = Graph()
    for edge in edges_data:
        u_id = edge["source"]
        v_id = edge["target"]

        if u_id in node_map and v_id in node_map:
            g.add_edge(node_map[u_id], node_map[v_id])
        else:
            logger.warning(f"Edge references unknown node(s): {u_id} -> {v_id}")

    # 3. Add any orphaned nodes (nodes with no edges)
    for node in node_map.values():
        if node not in g:
            g.add_node(node)

    logger.info(f"Loaded graph with {len(g)} nodes from JSON.")
    return g
