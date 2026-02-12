from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from shutil import which
from subprocess import PIPE, CalledProcessError, run
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable

logger = getLogger(__name__)


@dataclass
class D2StylingConfig:
    """
    Configuration for customizing D2 diagram generation.

    Attributes:
        node_ref_fnc: Function to generate the node identifier (reference).
        node_label_fnc: Function to generate the node label.
        node_style_fnc: Function to generate a dictionary of style attributes for a node.
        edge_style_fnc: Function to generate a dictionary of style attributes for an edge.
        global_style: Dictionary of global styling attributes.
        layout: D2 layout engine to use (e.g., 'dagre', 'elk').
        theme: D2 theme ID to use.
    """

    node_ref_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    node_label_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    node_style_fnc: Callable[[Graphable[Any]], dict[str, str]] | None = None
    edge_style_fnc: (
        Callable[[Graphable[Any], Graphable[Any]], dict[str, str]] | None
    ) = None
    global_style: dict[str, str] | None = None
    layout: str | None = None
    theme: str | None = None
    cluster_by_tag: bool = False
    tag_sort_fnc: Callable[[set[str]], list[str]] = lambda s: sorted(list(s))


def _check_d2_on_path() -> None:
    """Check if 'd2' executable is available in the system path."""
    if which("d2") is None:
        logger.error("d2 not found on PATH.")
        raise FileNotFoundError(
            "d2 is required but not available on $PATH. "
            "Install it via the official script: 'curl -fsSL https://d2lang.com/install.sh | sh -s --'."
        )


def _format_styles(styles: dict[str, str] | None, indent: str = "  ") -> list[str]:
    """Format a dictionary of styles into D2 style lines."""
    if not styles:
        return []
    lines = [f"{indent}style: {{"]
    for k, v in styles.items():
        lines.append(f"{indent}  {k}: {v}")
    lines.append(f"{indent}}}")
    return lines


def create_topology_d2(graph: Graph, config: D2StylingConfig | None = None) -> str:
    """
    Generate D2 definition from a Graph.

    Args:
        graph (Graph): The graph to convert.
        config (D2StylingConfig | None): Styling configuration.

    Returns:
        str: The D2 definition string.
    """
    config = config or D2StylingConfig()
    d2: list[str] = []

    if config.layout:
        d2.append(
            f"vars: {{\n  d2-config: {{\n    layout-engine: {config.layout}\n  }}\n}}"
        )

    if config.theme:
        d2.append("direction: down")  # Default direction

    def get_cluster(node: Graphable[Any]) -> str | None:
        if not config.cluster_by_tag or not node.tags:
            return None
        sorted_tags = config.tag_sort_fnc(node.tags)
        return sorted_tags[0] if sorted_tags else None

    # Group nodes by cluster
    clusters: dict[str | None, list[Graphable[Any]]] = {}
    for node in graph.topological_order():
        cluster = get_cluster(node)
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(node)

    # Nodes (potentially within clusters)
    for cluster_name, nodes in clusters.items():
        indent = ""
        if cluster_name:
            d2.append(f"{cluster_name}: {{")
            indent = "  "

        for node in nodes:
            node_ref = config.node_ref_fnc(node)
            node_label = config.node_label_fnc(node)
            d2.append(f"{indent}{node_ref}: {node_label}")

            if config.node_style_fnc:
                styles = config.node_style_fnc(node)
                d2.extend(_format_styles(styles, indent=indent + "  "))

        if cluster_name:
            d2.append("}")

    # Edges
    for node in graph.topological_order():
        node_ref = config.node_ref_fnc(node)
        for dependent in node.dependents:
            dep_ref = config.node_ref_fnc(dependent)
            # If nodes are in clusters, D2 handles flat references or nested references.
            # Usually, if IDs are unique, flat references work.
            # But if we wanted to be explicit: cluster.node_ref
            # For now, let's assume node_ref is globally unique (the default is reference string).
            edge_line = f"{node_ref} -> {dep_ref}"

            if config.edge_style_fnc:
                edge_styles = config.edge_style_fnc(node, dependent)
                if edge_styles:
                    d2.append(f"{edge_line}: {{")
                    d2.extend(_format_styles(edge_styles, indent="  "))
                    d2.append("}")
                else:
                    d2.append(edge_line)
            else:
                d2.append(edge_line)

    return "\n".join(d2)


def export_topology_d2(
    graph: Graph, output: Path, config: D2StylingConfig | None = None
) -> None:
    """
    Export the graph to a D2 file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (D2StylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting D2 definition to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_d2(graph, config))


def export_topology_d2_svg(
    graph: Graph, output: Path, config: D2StylingConfig | None = None
) -> None:
    """
    Export the graph to an SVG file using the 'd2' command.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (D2StylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting D2 svg to: {output}")
    _check_d2_on_path()

    d2_content: str = create_topology_d2(graph, config)

    cmd = ["d2"]
    if config and config.theme:
        cmd.extend(["--theme", config.theme])
    if config and config.layout:
        cmd.extend(["--layout", config.layout])

    cmd.extend(["-", str(output)])

    try:
        run(
            cmd,
            input=d2_content,
            check=True,
            stderr=PIPE,
            stdout=PIPE,
            text=True,
        )
        logger.info(f"Successfully exported SVG to {output}")
    except CalledProcessError as e:
        logger.error(f"Error executing d2: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Failed to export SVG to {output}: {e}")
        raise
