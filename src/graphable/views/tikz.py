from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable
from ..registry import register_view

logger = getLogger(__name__)


@dataclass
class TikzStylingConfig:
    """
    Configuration for customizing TikZ diagram generation.

    Attributes:
        node_ref_fnc: Function to generate the node identifier.
        node_label_fnc: Function to generate the node label.
        node_options: Global TikZ options for nodes.
        edge_options: Global TikZ options for edges.
        use_graphs_lib: Whether to use the TikZ 'graphs' library syntax.
    """

    node_ref_fnc: Callable[[Graphable[Any]], str] = lambda n: f"node_{id(n)}"
    node_label_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    node_options: str = "draw, circle"
    edge_options: str = "->"
    use_graphs_lib: bool = True


def create_topology_tikz(graph: Graph, config: TikzStylingConfig | None = None) -> str:
    """
    Generate TikZ LaTeX code from a Graph.

    Args:
        graph (Graph): The graph to convert.
        config (TikzStylingConfig | None): Styling configuration.

    Returns:
        str: The TikZ LaTeX code string.
    """
    config = config or TikzStylingConfig()
    lines: list[str] = [r"\begin{tikzpicture}"]

    if config.use_graphs_lib:
        lines.append(r"  \usetikzlibrary{graphs}")
        lines.append("  \\graph [nodes={" + config.node_options + "}] {")

        # Define nodes and edges in graph syntax
        for node in graph.topological_order():
            node_ref = config.node_ref_fnc(node)
            node_label = config.node_label_fnc(node)
            # TikZ graph syntax: alias/Label
            lines.append(f'    {node_ref} ["{node_label}"];')

            for dependent, _ in graph.internal_dependents(node):
                dep_ref = config.node_ref_fnc(dependent)
                lines.append(f"    {node_ref} -> {dep_ref};")

        lines.append("  };")
    else:
        # Standard TikZ syntax (simplified placement)
        for i, node in enumerate(graph.topological_order()):
            node_ref = config.node_ref_fnc(node)
            node_label = config.node_label_fnc(node)
            lines.append(
                f"  \\node[{config.node_options}] ({node_ref}) at (0,{-i * 1.5}) {{{node_label}}};"
            )

        for node in graph.topological_order():
            node_ref = config.node_ref_fnc(node)
            for dependent, _ in graph.internal_dependents(node):
                dep_ref = config.node_ref_fnc(dependent)
                lines.append(
                    f"  \\draw[{config.edge_options}] ({node_ref}) -- ({dep_ref});"
                )

    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


@register_view(".tex", creator_fnc=create_topology_tikz)
def export_topology_tikz(
    graph: Graph, output: Path, config: TikzStylingConfig | None = None
) -> None:
    """
    Export the graph to a TikZ (.tex) file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (TikZStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting TikZ definition to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_tikz(graph, config))
