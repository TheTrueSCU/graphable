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
class PlantUmlStylingConfig:
    """
    Configuration for customizing PlantUML diagram generation.

    Attributes:
        node_ref_fnc: Function to generate the node identifier (alias).
        node_label_fnc: Function to generate the node label.
        node_type: PlantUML node type (e.g., 'node', 'component', 'artifact').
        direction: Diagram direction (e.g., 'top to bottom direction', 'left to right direction').
    """

    node_ref_fnc: Callable[[Graphable[Any]], str] = lambda n: f"node_{id(n)}"
    node_label_fnc: Callable[[Graphable[Any]], str] = lambda n: str(n.reference)
    node_type: str = "node"
    direction: str = "top to bottom direction"
    cluster_by_tag: bool = False
    tag_sort_fnc: Callable[[set[str]], list[str]] = lambda s: sorted(list(s))


def _check_plantuml_on_path() -> None:
    """Check if 'plantuml' executable is available in the system path."""
    if which("plantuml") is None:
        logger.error("plantuml not found on PATH.")
        raise FileNotFoundError(
            "plantuml is required but not available on $PATH. "
            "Install it via your package manager (e.g., 'sudo apt install plantuml')."
        )


def create_topology_plantuml(
    graph: Graph, config: PlantUmlStylingConfig | None = None
) -> str:
    """
    Generate PlantUML definition from a Graph.

    Args:
        graph (Graph): The graph to convert.
        config (PlantUmlStylingConfig | None): Styling configuration.

    Returns:
        str: The PlantUML definition string.
    """
    config = config or PlantUmlStylingConfig()
    puml: list[str] = ["@startuml", f"{config.direction}"]

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
            puml.append(f'package "{cluster_name}" {{')
            indent = "  "

        for node in nodes:
            node_ref = config.node_ref_fnc(node)
            node_label = config.node_label_fnc(node)
            puml.append(f'{indent}{config.node_type} "{node_label}" as {node_ref}')

        if cluster_name:
            puml.append("}")

    # Edges
    for node in graph.topological_order():
        node_ref = config.node_ref_fnc(node)
        for dependent, _ in graph.internal_dependents(node):
            dep_ref = config.node_ref_fnc(dependent)
            puml.append(f"{node_ref} --> {dep_ref}")

    puml.append("@enduml")
    return "\n".join(puml)


@register_view(".puml", creator_fnc=create_topology_plantuml)
def export_topology_plantuml(
    graph: Graph, output: Path, config: PlantUmlStylingConfig | None = None
) -> None:
    """
    Export the graph to a PlantUML (.puml) file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (PlantUMLStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting PlantUML definition to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_plantuml(graph, config))


@register_view([".svg", ".png"])
def export_topology_plantuml_image(
    graph: Graph, output: Path, config: PlantUmlStylingConfig | None = None
) -> None:
    """
    Export the graph to an image file (SVG or PNG) using the 'plantuml' command.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (PlantUmlStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting PlantUML image to: {output}")
    _check_plantuml_on_path()

    p = Path(output)
    puml_content: str = create_topology_plantuml(graph, config)

    fmt = p.suffix[1:].lower()

    try:
        run(
            ["plantuml", f"-t{fmt}", "-p"],
            input=puml_content,
            check=True,
            stderr=PIPE,
            stdout=open(p, "wb"),
            text=True,
        )
        logger.info(f"Successfully exported {fmt.upper()} to {output}")
    except CalledProcessError as e:
        logger.error(f"Error executing plantuml: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Failed to export {fmt.upper()} to {output}: {e}")
        raise
