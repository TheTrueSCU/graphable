from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..registry import register_parser
from .utils import build_graph_from_data, is_path

logger = getLogger(__name__)


@register_parser(".toml")
def load_graph_toml(source: str | Path, reference_type: type = str) -> Graph[Any]:
    """
    Load a graph from a TOML string or file.
    Uses 'tomllib' (Python 3.11+) or 'tomli'.

    Args:
        source: TOML string or path to a TOML file.
        reference_type: The type to cast the node reference to (default: str).

    Returns:
        Graph: A new Graph instance populated from the TOML data.
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            logger.error("No TOML parser found. On Python < 3.11, install 'tomli'.")
            raise ImportError(
                "TOML parsing requires 'tomllib' (Python 3.11+) or 'tomli'."
            )

    if is_path(source):
        logger.debug(f"Loading TOML from file: {source}")
        with open(source, "rb") as f:
            data = tomllib.load(f)
    else:
        logger.debug("Loading TOML from string.")
        data = tomllib.loads(str(source))

    # Handle wrapped structure
    if "graph" in data and ("nodes" not in data or "edges" not in data):
        data = data["graph"]

    nodes_data = data.get("nodes", [])
    edges_data = data.get("edges", [])

    g = build_graph_from_data(nodes_data, edges_data, reference_type)
    logger.info(f"Loaded graph with {len(g)} nodes from TOML.")
    return g
