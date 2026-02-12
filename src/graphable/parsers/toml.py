import tomllib
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..graphable import Graphable
from .utils import is_path

logger = getLogger(__name__)


def load_graph_toml(
    source: str | Path, reference_type: type = str
) -> Graph[Graphable[Any]]:
    """
    Load a graph from a TOML string or file.

    Args:
        source: TOML string or path to a TOML file.
        reference_type: The type to cast the node reference to (default: str).

    Returns:
        Graph: A new Graph instance populated from the TOML data.
    """
    if is_path(source):
        logger.debug(f"Loading TOML from file: {source}")
        with open(source, "rb") as f:
            data = tomllib.load(f)
    else:
        logger.debug("Loading TOML from string.")
        data = tomllib.loads(str(source))

    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])

    # 1. Create all nodes
    node_map: dict[str, Graphable[Any]] = {}
    for entry in nodes_data:
        node_id = str(entry["id"])
        reference = entry.get("reference", node_id)

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
        u_id = str(edge["source"])
        v_id = str(edge["target"])

        if u_id in node_map and v_id in node_map:
            g.add_edge(node_map[u_id], node_map[v_id])
        else:
            logger.warning(f"Edge references unknown node(s): {u_id} -> {v_id}")

    # 3. Add any orphaned nodes
    for node in node_map.values():
        if node not in g:
            g.add_node(node)

    logger.info(f"Loaded graph with {len(g)} nodes from TOML.")
    return g
