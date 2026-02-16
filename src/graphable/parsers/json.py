from json import load, loads
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..registry import register_parser
from .utils import build_graph_from_data, is_path

logger = getLogger(__name__)


@register_parser(".json")
def load_graph_json(source: str | Path, reference_type: type = str) -> Graph[Any]:
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
            data = load(f)
    else:
        logger.debug("Loading JSON from string.")
        data = loads(str(source))

    # Handle wrapped structure: {"checksum": "...", "graph": {"nodes": ..., "edges": ...}}
    if "graph" in data and ("nodes" not in data or "edges" not in data):
        logger.debug("Detected wrapped JSON structure, extracting 'graph' object.")
        data = data["graph"]

    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])

    g = build_graph_from_data(nodes_data, edges_data, reference_type)
    logger.info(f"Loaded graph with {len(g)} nodes from JSON.")
    return g
