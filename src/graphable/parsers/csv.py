import csv
import io
from logging import getLogger
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..registry import register_parser
from .utils import build_graph_from_data, is_path

logger = getLogger(__name__)


@register_parser(".csv")
def load_graph_csv(source: str | Path, reference_type: type = str) -> Graph[Any]:
    """
    Load a Graph from a CSV edge list.

    Args:
        source: CSV string or path to a CSV file.
        reference_type: The type to cast the reference string to.

    Returns:
        Graph: The loaded Graph instance.
    """
    if is_path(source):
        with open(source, "r", newline="") as f:
            content = f.read()
    else:
        content = str(source)

    f = io.StringIO(content.strip())
    reader = csv.reader(f)

    # Detect header
    first_row = next(reader, None)
    if not first_row:
        return Graph()

    edges_data = []
    # Check if first row is header
    if first_row == ["source", "target"]:
        # Standard header
        pass
    else:
        # No header, treat first row as data
        edges_data.append({"source": first_row[0], "target": first_row[1]})

    for row in reader:
        if len(row) >= 2:
            edges_data.append({"source": row[0], "target": row[1]})

    # Collect unique node IDs from edges
    node_ids = set()
    for edge in edges_data:
        node_ids.add(edge["source"])
        node_ids.add(edge["target"])

    nodes_data = [{"id": nid} for nid in node_ids]

    g = build_graph_from_data(nodes_data, edges_data, reference_type)
    logger.info(f"Loaded graph with {len(g)} nodes from CSV.")
    return g
