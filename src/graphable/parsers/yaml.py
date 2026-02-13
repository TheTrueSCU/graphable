from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..registry import register_parser
from .utils import build_graph_from_data, is_path

logger = getLogger(__name__)


@register_parser([".yaml", ".yml"])
def load_graph_yaml(source: str | Path, reference_type: type = str) -> Graph[Any]:
    """
    Load a graph from a YAML string or file.
    Requires 'PyYAML' to be installed.

    Args:
        source: YAML string or path to a YAML file.
        reference_type: The type to cast the node reference to (default: str).

    Returns:
        Graph: A new Graph instance populated from the YAML data.
    """
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML not found. Please install it with 'pip install PyYAML'.")
        raise ImportError(
            "PyYAML is required for YAML parsing. Install it with 'pip install PyYAML'."
        )

    if is_path(source):
        logger.debug(f"Loading YAML from file: {source}")
        with open(source, "r") as f:
            data = yaml.safe_load(f)
    else:
        logger.debug("Loading YAML from string.")
        data = yaml.safe_load(str(source))

    # Handle wrapped structure
    if "graph" in data and ("nodes" not in data or "edges" not in data):
        data = data["graph"]

    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])

    g = build_graph_from_data(nodes_data, edges_data, reference_type)
    logger.info(f"Loaded graph with {len(g)} nodes from YAML.")
    return g
