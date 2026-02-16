from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from shutil import which
from subprocess import PIPE, CalledProcessError, run
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable
from ..registry import register_view

logger = getLogger(__name__)


@dataclass
class GraphvizStylingConfig:
    """
    Configuration for customizing Graphviz DOT generation.

    Attributes:
        node_ref_fnc: Function to generate the node identifier (reference).
        node_label_fnc: Function to generate the node label.
        node_attr_fnc: Function to generate a dictionary of attributes for a node.
        edge_attr_fnc: Function to generate a dictionary of attributes for an edge.
        graph_attr: Dictionary of global graph attributes.
        node_attr_default: Dictionary of default node attributes.
        edge_attr_default: Dictionary of default edge attributes.
    """

    node_ref_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    node_label_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    node_attr_fnc: Callable[[Graphable[Any]], dict[str, str]] | None = None
    edge_attr_fnc: Callable[[Graphable[Any], Graphable[Any]], dict[str, str]] | None = (
        None
    )
    graph_attr: dict[str, str] | None = None
    node_attr_default: dict[str, str] | None = None
    edge_attr_default: dict[str, str] | None = None
    cluster_by_tag: bool = False
    tag_sort_fnc: Callable[[set[str]], list[str]] = lambda s: sorted(list(s))


def _check_dot_on_path() -> None:
    """Check if 'dot' executable is available in the system path."""
    if which("dot") is None:
        logger.error("dot not found on PATH.")
        raise FileNotFoundError(
            "dot (Graphviz) is required but not available on $PATH. "
            "Install it via your package manager (e.g., 'sudo apt install graphviz')."
        )


def _format_attrs(attrs: dict[str, str] | None) -> str:
    """Format a dictionary of attributes into a DOT attribute string."""
    if not attrs:
        return ""
    parts = [f'{k}="{v}"' for k, v in attrs.items()]
    return f" [{', '.join(parts)}]"


def create_topology_graphviz_dot(
    graph: Graph, config: GraphvizStylingConfig | None = None
) -> str:
    """
    Generate Graphviz DOT definition from a Graph.

    Args:
        graph (Graph): The graph to convert.
        config (GraphvizStylingConfig | None): Styling configuration.

    Returns:
        str: The Graphviz DOT definition string.
    """
    config = config or GraphvizStylingConfig()
    dot: list[str] = ["digraph G {"]

    # Global attributes
    if config.graph_attr:
        for k, v in config.graph_attr.items():
            dot.append(f'    {k}="{v}";')

    if config.node_attr_default:
        dot.append(f"    node{_format_attrs(config.node_attr_default)};")

    if config.edge_attr_default:
        dot.append(f"    edge{_format_attrs(config.edge_attr_default)};")

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
        indent = "    "
        if cluster_name:
            dot.append(f'    subgraph "cluster_{cluster_name}" {{')
            dot.append(f'        label="{cluster_name}";')
            indent = "        "

        for node in nodes:
            node_ref = config.node_ref_fnc(node)
            node_attrs = {"label": config.node_label_fnc(node)}
            if config.node_attr_fnc:
                node_attrs.update(config.node_attr_fnc(node))

            dot.append(f'{indent}"{node_ref}"{_format_attrs(node_attrs)};')

        if cluster_name:
            dot.append("    }")

    # Edges
    for node in graph.topological_order():
        node_ref = config.node_ref_fnc(node)
        for dependent, attrs in graph.internal_dependents(node):
            dep_ref = config.node_ref_fnc(dependent)
            edge_attrs = {}
            if config.edge_attr_fnc:
                edge_attrs.update(config.edge_attr_fnc(node, dependent))

            dot.append(f'    "{node_ref}" -> "{dep_ref}"{_format_attrs(edge_attrs)};')

    dot.append("}")
    return "\n".join(dot)


@register_view([".dot", ".gv"], creator_fnc=create_topology_graphviz_dot)
def export_topology_graphviz_dot(
    graph: Graph, output: Path, config: GraphvizStylingConfig | None = None
) -> None:
    """
    Export the graph to a Graphviz .dot file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (GraphvizStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting graphviz dot to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_graphviz_dot(graph, config))


@register_view([".svg", ".png"])
def export_topology_graphviz_image(
    graph: Graph, output: Path, config: GraphvizStylingConfig | None = None
) -> None:
    """
    Export the graph to an image file (SVG or PNG) using the 'dot' command.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (GraphvizStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting graphviz image to: {output}")
    _check_dot_on_path()

    p = Path(output)
    dot_content: str = create_topology_graphviz_dot(graph, config)

    # Extension without dot
    fmt = p.suffix[1:].lower()

    try:
        run(
            ["dot", f"-T{fmt}", "-o", str(p)],
            input=dot_content,
            check=True,
            stderr=PIPE,
            stdout=PIPE,
            text=True,
        )
        logger.info(f"Successfully exported {fmt.upper()} to {output}")
    except CalledProcessError as e:
        logger.error(f"Error executing dot: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Failed to export {fmt.upper()} to {output}: {e}")
        raise
