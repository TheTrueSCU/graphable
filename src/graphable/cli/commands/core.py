from pathlib import Path
from typing import Any, Callable

from ...graph import Graph
from ...parsers.csv import load_graph_csv
from ...parsers.graphml import load_graph_graphml
from ...parsers.json import load_graph_json
from ...parsers.toml import load_graph_toml
from ...parsers.yaml import load_graph_yaml
from ...views.asciiflow import export_topology_ascii_flow
from ...views.csv import export_topology_csv
from ...views.d2 import export_topology_d2
from ...views.graphml import export_topology_graphml
from ...views.graphviz import export_topology_graphviz_dot
from ...views.html import export_topology_html
from ...views.json import export_topology_json
from ...views.mermaid import export_topology_mermaid_mmd, export_topology_mermaid_svg
from ...views.plantuml import export_topology_plantuml
from ...views.texttree import export_topology_tree_txt
from ...views.tikz import export_topology_tikz
from ...views.toml import export_topology_toml
from ...views.yaml import export_topology_yaml


def get_parser(extension: str) -> Callable[..., Graph[Any]]:
    parsers = {
        ".json": load_graph_json,
        ".yaml": load_graph_yaml,
        ".yml": load_graph_yaml,
        ".toml": load_graph_toml,
        ".csv": load_graph_csv,
        ".graphml": load_graph_graphml,
    }
    parser = parsers.get(extension.lower())
    if not parser:
        raise ValueError(f"No parser available for extension: {extension}")
    return parser


def get_exporter(extension: str) -> Callable[..., None] | None:
    exporters = {
        ".json": export_topology_json,
        ".yaml": export_topology_yaml,
        ".yml": export_topology_yaml,
        ".toml": export_topology_toml,
        ".csv": export_topology_csv,
        ".graphml": export_topology_graphml,
        ".dot": export_topology_graphviz_dot,
        ".gv": export_topology_graphviz_dot,
        ".svg": None,  # Needs special handling based on what tool is available
        ".mmd": export_topology_mermaid_mmd,
        ".d2": export_topology_d2,
        ".puml": export_topology_plantuml,
        ".html": export_topology_html,
        ".tex": export_topology_tikz,
        ".txt": export_topology_tree_txt,
        ".ascii": export_topology_ascii_flow,
    }

    return exporters.get(extension.lower())


def load_graph(path: Path) -> Graph[Any]:
    parser = get_parser(path.suffix)
    return parser(path)


def info_command(path: Path) -> dict[str, Any]:
    g = load_graph(path)
    return {
        "nodes": len(g),
        "edges": sum(len(node.dependents) for node in g),
        "sources": [n.reference for n in g.sources],
        "sinks": [n.reference for n in g.sinks],
    }


def check_command(path: Path) -> dict[str, Any]:
    try:
        g = load_graph(path)
        g.check_cycles()
        g.check_consistency()
        return {"valid": True, "error": None}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def reduce_command(input_path: Path, output_path: Path) -> None:
    g = load_graph(input_path)
    reduced = g.transitive_reduction()

    if output_path.suffix == ".svg":
        # Default to mermaid for SVG reduction if not specified
        export_topology_mermaid_svg(reduced, output_path)
    elif exporter := get_exporter(output_path.suffix):
        exporter(reduced, output_path)
    else:
        raise ValueError(f"No exporter available for extension: {output_path.suffix}")


def convert_command(input_path: Path, output_path: Path, **kwargs: Any) -> None:
    g = load_graph(input_path)

    if output_path.suffix == ".svg":
        # Determine which SVG exporter to use
        # Default to mermaid
        export_topology_mermaid_svg(g, output_path, **kwargs)
    elif exporter := get_exporter(output_path.suffix):
        exporter(g, output_path, **kwargs)
    else:
        raise ValueError(f"No exporter available for extension: {output_path.suffix}")
