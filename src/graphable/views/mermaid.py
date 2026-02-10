from atexit import register as on_script_exit
from dataclasses import dataclass
from functools import cache
from logging import getLogger
from pathlib import Path
from shutil import which
from string import Template
from subprocess import PIPE, CalledProcessError, run
from tempfile import NamedTemporaryFile
from typing import Any, Callable

from ..graph import Graph
from ..graphable import Graphable

logger = getLogger(__name__)

_MERMAID_CONFIG_JSON: str = '{ "htmlLabels": false }'
_MMDC_SCRIPT_TEMPLATE: Template = Template("""
#!/bin/env bash
/bin/env mmdc -c $mermaid_config -i $source -o $output -p $puppeteer_config
""")
_PUPPETEER_CONFIG_JSON: str = '{ "args": [ "--no-sandbox" ] }'


@dataclass
class MermaidStylingConfig:
    """
    Configuration for customizing Mermaid diagram generation.

    Attributes:
        node_ref_fnc: Function to generate the node identifier (reference).
        node_text_fnc: Function to generate the node label text.
        node_style_fnc: Function to generate specific style for a node (or None).
        node_style_default: Default style string for nodes (or None).
        link_text_fnc: Function to generate label for links between nodes.
        link_style_fnc: Function to generate style for links (or None).
        link_style_default: Default style string for links (or None).
    """

    node_ref_fnc: Callable[[Graphable[Any]], str] = lambda n: n.reference
    node_text_fnc: Callable[[Graphable[Any]], str] = lambda n: n.reference
    node_style_fnc: Callable[[Graphable[Any]], str] | None = None
    node_style_default: str | None = None
    link_text_fnc: Callable[[Graphable[Any], Graphable[Any]], str] = lambda n, sn: "-->"
    link_style_fnc: Callable[[Graphable[Any], Graphable[Any]], str] | None = None
    link_style_default: str | None = None


def _check_mmdc_on_path() -> None:
    """Check if 'mmdc' executable is available in the system path."""
    if which("mmdc") is None:
        logger.error("mmdc not found on PATH.")
        raise FileNotFoundError(
            "mmdc (Mermaid CLI) is required but not available on $PATH. "
            "Install it via npm: 'npm install -g @mermaid-js/mermaid-cli'."
        )


def _cleanup_on_exit(path: Path) -> None:
    """
    Remove a temporary file if it still exists at script exit.

    Args:
        path (Path): The path to the file to remove.
    """
    if path.exists():
        logger.debug(f"Cleaning up temporary file: {path}")
        path.unlink()


def _create_mmdc_script(mmdc_script_content: str) -> Path:
    """Create a temporary shell script for executing mmdc."""
    with NamedTemporaryFile(delete=False, mode="w+", suffix=".sh") as f:
        f.write(mmdc_script_content)
        mmdc_script: Path = Path(f.name)
    logger.debug(f"Created temporary mmdc script: {mmdc_script}")
    return mmdc_script


def create_mmdc_script_content(source: Path, output: Path) -> str:
    """
    Generate the bash script content to run mmdc.

    Args:
        source (Path): Path to the source mermaid file.
        output (Path): Path to the output file.

    Returns:
        str: The script content.
    """
    mmdc_script_content: str = _MMDC_SCRIPT_TEMPLATE.substitute(
        mermaid_config=_write_mermaid_config(),
        output=output,
        puppeteer_config=_write_puppeteer_config(),
        source=source,
    )

    return mmdc_script_content


def create_topology_mermaid_mmd(
    graph: Graph, config: MermaidStylingConfig | None = None
) -> str:
    """
    Generate Mermaid flowchart definition from a Graph.

    Args:
        graph (Graph): The graph to convert.
        config (MermaidStylingConfig | None): Styling configuration.

    Returns:
        str: The mermaid graph definition string.
    """
    config = config or MermaidStylingConfig()

    def link_style(node: Graphable[Any], subnode: Graphable[Any]) -> str | None:
        if config.link_style_fnc:
            return config.link_style_fnc(node, subnode)
        return None

    def node_style(node: Graphable[Any]) -> str | None:
        if config.node_style_fnc and (style := config.node_style_fnc(node)):
            return style
        return config.node_style_default

    link_num: int = 0
    mermaid: list[str] = ["flowchart TD"]
    for node in graph.topological_order():
        if subnodes := node.dependents:
            for subnode in subnodes:
                mermaid.append(
                    f"{config.node_text_fnc(node)} {config.link_text_fnc(node, subnode)} {config.node_text_fnc(subnode)}"
                )
                if style := link_style(node, subnode):
                    mermaid.append(f"linkStyle {link_num} {style}")
                link_num += 1
        else:
            mermaid.append(f"{config.node_text_fnc(node)}")

        if style := node_style(node):
            mermaid.append(f"style {config.node_ref_fnc(node)} {style}")

    if config.link_style_default:
        mermaid.append(f"linkStyle default {config.link_style_default}")

    return "\n".join(mermaid)


def _execute_build_script(build_script: Path) -> bool:
    """
    Execute the build script.

    Args:
        build_script (Path): Path to the script.

    Returns:
        bool: True if execution succeeded, False otherwise.
    """
    try:
        run(
            ["/bin/env", "bash", build_script],
            check=True,
            stderr=PIPE,
            stdout=PIPE,
            text=True,
        )
        return True
    except CalledProcessError as e:
        logger.error(f"Error executing {build_script}: {e.stderr}")
    except FileNotFoundError:
        logger.error("Could not execute script: file not found.")
    return False


def export_topology_mermaid_mmd(
    graph: Graph, output: Path, config: MermaidStylingConfig | None = None
) -> None:
    """
    Export the graph to a Mermaid .mmd file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (MermaidStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting mermaid mmd to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_mermaid_mmd(graph, config))


def export_topology_mermaid_svg(
    graph: Graph, output: Path, config: MermaidStylingConfig | None = None
) -> None:
    """
    Export the graph to an SVG file using mmdc.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (MermaidStylingConfig | None): Styling configuration.
    """
    logger.info(f"Exporting mermaid svg to: {output}")
    _check_mmdc_on_path()

    mermaid: str = create_topology_mermaid_mmd(graph, config)

    with NamedTemporaryFile(delete=False, mode="w+", suffix=".mmd") as f:
        f.write(mermaid)
        source: Path = Path(f.name)

    logger.debug(f"Created temporary mermaid source file: {source}")

    build_script: Path = _create_mmdc_script(
        create_mmdc_script_content(source=source, output=output)
    )

    if _execute_build_script(build_script):
        build_script.unlink()
        source.unlink()
        logger.info(f"Successfully exported SVG to {output}")
    else:
        logger.error(f"Failed to export SVG to {output}")


@cache
def _write_mermaid_config() -> Path:
    """Write temporary mermaid config file."""
    with NamedTemporaryFile(delete=False, mode="w+", suffix=".json") as f:
        f.write(_MERMAID_CONFIG_JSON)

        path: Path = Path(f.name)
        on_script_exit(lambda: _cleanup_on_exit(path))
        return path


@cache
def _write_puppeteer_config() -> Path:
    """Write temporary puppeteer config file."""
    with NamedTemporaryFile(delete=False, mode="w+", suffix=".json") as f:
        f.write(_PUPPETEER_CONFIG_JSON)

        path: Path = Path(f.name)
        on_script_exit(lambda: _cleanup_on_exit(path))
        return path
