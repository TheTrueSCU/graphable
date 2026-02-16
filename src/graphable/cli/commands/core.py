from pathlib import Path
from typing import Any, Callable

from ...enums import Engine
from ...graph import Graph
from ...registry import EXPORTERS, PARSERS


def get_parser(extension: str) -> Callable[..., Graph[Any]]:
    parser = PARSERS.get(extension.lower())
    if not parser:
        raise ValueError(f"No parser available for extension: {extension}")
    return parser


def get_exporter(extension: str) -> Callable[..., None] | None:
    return EXPORTERS.get(extension.lower())


def load_graph(path: Path, tag: str | None = None) -> Graph[Any]:
    parser = get_parser(path.suffix)
    g = parser(path)
    if tag:
        g = g.subgraph_tagged(tag)
    return g


def info_command(path: Path, tag: str | None = None) -> dict[str, Any]:
    g = load_graph(path, tag)

    stats = {
        "nodes": len(g),
        "edges": sum(len(node.dependents) for node in g),
        "sources": [n.reference for n in g.sources],
        "sinks": [n.reference for n in g.sinks],
        "project_duration": None,
        "critical_path_length": 0,
    }

    # Check if we should run CPM (if any node has duration > 0)
    if any(n.duration > 0 for n in g):
        analysis = g.cpm_analysis()
        stats["project_duration"] = max((v["EF"] for v in analysis.values()), default=0)
        stats["critical_path_length"] = len(g.critical_path())

    return stats


def check_command(path: Path, tag: str | None = None) -> dict[str, Any]:
    try:
        g = load_graph(path, tag)
        g.check_cycles()
        g.check_consistency()
        return {"valid": True, "error": None}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def reduce_command(
    input_path: Path,
    output_path: Path,
    embed_checksum: bool = False,
    tag: str | None = None,
) -> None:
    g = load_graph(input_path, tag)
    g.write(output_path, transitive_reduction=True, embed_checksum=embed_checksum)


def convert_command(
    input_path: Path, output_path: Path, tag: str | None = None, **kwargs: Any
) -> None:
    # Restrict convert to non-image formats
    ext = output_path.suffix.lower()
    if ext in (".png", ".svg"):
        raise ValueError(
            f"Extension '{ext}' is for images. Use the 'render' command instead."
        )

    g = load_graph(input_path, tag)
    g.write(output_path, **kwargs)


def checksum_command(path: Path, tag: str | None = None) -> str:
    g = load_graph(path, tag)
    return g.checksum()


def verify_command(
    path: Path, expected: str | None = None, tag: str | None = None
) -> dict[str, Any]:
    g = load_graph(path, tag)
    actual = g.checksum()

    if expected is None:
        # Check if there is an embedded checksum
        from ...parsers.utils import extract_checksum

        expected = extract_checksum(path)

    if expected is None:
        return {"valid": None, "actual": actual, "expected": None}

    return {"valid": actual == expected, "actual": actual, "expected": expected}


def write_checksum_command(
    graph_path: Path, checksum_path: Path, tag: str | None = None
) -> None:
    g = load_graph(graph_path, tag)
    g.write_checksum(checksum_path)


def diff_command(path1: Path, path2: Path, tag: str | None = None) -> dict[str, Any]:
    g1 = load_graph(path1, tag)
    g2 = load_graph(path2, tag)
    return g1.diff(g2)


def diff_visual_command(
    path1: Path, path2: Path, output_path: Path, tag: str | None = None
) -> None:
    g1 = load_graph(path1, tag)
    g2 = load_graph(path2, tag)
    dg = g1.diff_graph(g2)
    dg.write(output_path)


def render_command(
    input_path: Path,
    output_path: Path,
    engine: Engine | str | None = None,
    tag: str | None = None,
) -> None:
    """
    Load a graph and render it as an image (SVG or PNG).

    Args:
        input_path: Path to the input graph file.
        output_path: Path to the output image file.
        engine: The rendering engine to use (e.g., Engine.MERMAID, 'graphviz').
            If None, it will be auto-detected based on system PATH.
        tag: Optional tag to filter the graph before rendering.
    """
    g = load_graph(input_path, tag)

    from ...views.utils import get_image_exporter

    exporter = get_image_exporter(engine)
    exporter(g, output_path)
