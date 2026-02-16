from pathlib import Path
from typing import Any, Callable

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
    engine: str | None = None,
    tag: str | None = None,
) -> None:
    g = load_graph(input_path, tag)

    if engine is None:
        from ...views.utils import detect_engine

        engine = detect_engine()

    engine = engine.lower()

    if engine == "mermaid":
        from ...views.mermaid import export_topology_mermaid_svg as exporter
    elif engine == "graphviz":
        from ...views.graphviz import export_topology_graphviz_svg as exporter
    elif engine == "d2":
        from ...views.d2 import export_topology_d2_svg as exporter
    elif engine == "plantuml":
        from ...views.plantuml import export_topology_plantuml_svg as exporter
    else:
        raise ValueError(f"Unknown engine: {engine}")

    exporter(g, output_path)
