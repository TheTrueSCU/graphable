import csv
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..graphable import Graphable
from .utils import is_path

logger = getLogger(__name__)


def load_graph_csv(
    source: str | Path, reference_type: type = str
) -> Graph[Graphable[Any]]:
    """
    Load a graph from a CSV file containing an edge list.
    Expected format: source,target (with optional header).

    Args:
        source: Path to a CSV file or CSV string.
        reference_type: The type to cast the node reference to (default: str).

    Returns:
        Graph: A new Graph instance populated from the CSV data.
    """
    if is_path(source):
        logger.debug(f"Loading CSV from file: {source}")
        with open(source, "r", newline="") as f:
            lines = f.readlines()
    else:
        logger.debug("Loading CSV from string.")
        lines = str(source).strip().splitlines()

    if not lines:
        return Graph()

    # Detect header
    has_header = False
    first_line = lines[0].lower()
    if "source" in first_line and "target" in first_line:
        has_header = True

    reader = csv.reader(lines[1:] if has_header else lines)

    g = Graph()
    node_map: dict[str, Graphable[Any]] = {}

    def get_or_create_node(ref_str: str) -> Graphable[Any]:
        if ref_str not in node_map:
            try:
                typed_ref = reference_type(ref_str)
            except (ValueError, TypeError):
                typed_ref = ref_str
            node_map[ref_str] = Graphable(typed_ref)
        return node_map[ref_str]

    for row in reader:
        if len(row) < 2:
            continue

        u_str, v_str = row[0].strip(), row[1].strip()
        if not u_str or not v_str:
            continue

        u = get_or_create_node(u_str)
        v = get_or_create_node(v_str)

        # add_edge also adds nodes to graph if not present
        g.add_edge(u, v)

    # Ensure all discovered nodes are in the graph (even if they only appeared as dependents)
    for node in node_map.values():
        if node not in g:
            g.add_node(node)

    logger.info(f"Loaded graph with {len(g)} nodes from CSV.")
    return g
