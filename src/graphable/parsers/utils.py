import re
from pathlib import Path
from typing import Any

from ..graph import Graph
from ..graphable import Graphable


def build_graph_from_data(
    nodes_data: list[dict[str, Any]],
    edges_data: list[dict[str, Any]],
    reference_type: type = str,
) -> Graph[Any]:
    """
    Standardized helper to construct a Graph from raw data.

    Args:
        nodes_data: List of node dictionaries (id, tags, duration, status).
        edges_data: List of edge dictionaries (source, target, attributes).
        reference_type: Type to cast the reference string to.

    Returns:
        Graph: The constructed Graph instance.
    """
    node_map: dict[str, Graphable[Any]] = {}

    # 1. Create nodes
    for node_entry in nodes_data:
        node_id = str(node_entry["id"])
        # Use provided reference if available, otherwise fallback to id
        ref_val = node_entry.get("reference", node_id)
        if reference_type is not str:
            try:
                ref_val = reference_type(ref_val)
            except (ValueError, TypeError):
                pass

        node = Graphable(ref_val)

        # Metadata
        for tag in node_entry.get("tags", []):
            node.add_tag(tag)

        if "duration" in node_entry:
            node.duration = float(node_entry["duration"])
        if "status" in node_entry:
            node.status = str(node_entry["status"])

        node_map[node_id] = node

    # 2. Link edges
    g = Graph(set(node_map.values()))
    for edge_entry in edges_data:
        u_id = str(edge_entry["source"])
        v_id = str(edge_entry["target"])

        if u_id in node_map and v_id in node_map:
            # All other keys are attributes
            attrs = {
                k: v for k, v in edge_entry.items() if k not in ("source", "target")
            }
            g.add_edge(node_map[u_id], node_map[v_id], **attrs)

    return g


def is_path(source: str | Path) -> bool:
    """
    Check if the given source is likely a path to a file.

    Args:
        source: The source to check (string or Path object).

    Returns:
        bool: True if it's a Path object or a string that points to an existing file.
    """
    if isinstance(source, Path):
        return True

    if isinstance(source, str) and "\n" not in source and len(source) < 1024:
        try:
            return Path(source).exists()
        except OSError:
            pass

    return False


def extract_checksum(source: str | Path) -> str | None:
    """
    Extract a blake2b checksum from the first few lines of a source.
    Looks for the pattern 'blake2b: <hash>'.

    Args:
        source: The source to check (string or Path object).

    Returns:
        str | None: The hash if found, otherwise None.
    """
    content = ""
    if is_path(source):
        try:
            # Read only the first 1KB to find comments
            with open(source, "r") as f:
                content = f.read(1024)
        except Exception:
            return None
    else:
        content = str(source)[:1024]

    # Match blake2b: followed by hex chars (usually 128 for blake2b)
    match = re.search(r"blake2b:\s*([a-fA-F0-9]+)", content)
    if match:
        return match.group(1)

    return None
