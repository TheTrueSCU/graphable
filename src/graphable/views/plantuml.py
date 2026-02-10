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

    # Nodes
    for node in graph.topological_order():
        node_ref = config.node_ref_fnc(node)
        node_label = config.node_label_fnc(node)
        puml.append(f'{config.node_type} "{node_label}" as {node_ref}')

    # Edges
    for node in graph.topological_order():
        node_ref = config.node_ref_fnc(node)
        for dependent in node.dependents:
            dep_ref = config.node_ref_fnc(dependent)
            puml.append(f"{node_ref} --> {dep_ref}")

    puml.append("@enduml")
    return "\n".join(puml)


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


def export_topology_plantuml_svg(
    graph: Graph, output: Path, config: PlantUmlStylingConfig | None = None
) -> None:
    """
    Export the graph to an SVG file using the 'plantuml' command.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (PlantUMLStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting PlantUML svg to: {output}")
    _check_plantuml_on_path()

    puml_content: str = create_topology_plantuml(graph, config)

    try:
        run(
            ["plantuml", "-tsvg", "-p"],
            input=puml_content,
            check=True,
            stderr=PIPE,
            stdout=open(output, "wb"),
            text=True,
        )
        logger.info(f"Successfully exported SVG to {output}")
    except CalledProcessError as e:
        logger.error(f"Error executing plantuml: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Failed to export SVG to {output}: {e}")
        raise
