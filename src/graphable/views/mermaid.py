from atexit import register as on_script_exit
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from shutil import which
from string import Template
from subprocess import CalledProcessError, PIPE, run
from tempfile import NamedTemporaryFile
from typing import Callable

from ..graph import Graph
from ..graphable import Graphable


_MERMAID_CONFIG_JSON: str = '{ "htmlLabels": false }'
_MMDC_SCRIPT_TEMPLATE: Template = Template("""
#!/bin/env bash
/bin/env mmdc -c $mermaid_config -i $source -o $output -p $puppeteer_config
""")
_PUPPETEER_CONFIG_JSON: str = '{ "args": [ "--no-sandbox" ] }'


@dataclass
class MermaidStylingConfig:
    node_ref_fnc: Callable[[Graphable], str] = lambda n: n.reference
    node_text_fnc: Callable[[Graphable], str] = lambda n: n.reference
    node_style_fnc: Callable[[Graphable], str] | None = None
    node_style_default: str | None = None
    link_text_fnc: Callable[[Graphable, Graphable], str] = lambda n, sn: "-->"
    link_style_fnc: Callable[[Graphable, Graphable], str] | None = None
    link_style_default: str | None = None


def _check_mmdc_on_path() -> None:
    if which("mmdc") is None:
        raise FileNotFoundError("mmdc is required but not available on $PATH")


def _create_mmdc_script(mmdc_script_content: str) -> Path:
    with NamedTemporaryFile(delete=False, mode="w+", suffix=".sh") as f:
        f.write(mmdc_script_content)
        mmdc_script: Path = Path(f.name)
    return mmdc_script


def create_mmdc_script_content(source: Path, output: Path) -> str:
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
    config = config or MermaidStylingConfig()

    def link_style(node: Graphable, subnode: Graphable) -> str | None:
        if config.link_style_fnc:
            return config.link_style_fnc(node, subnode)
        return None

    def node_style(node: Graphable) -> str | None:
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
    try:
        run(
            ["/bin/env", "bash", build_script],
            check=True,
            stderr=PIPE,
            stdout=PIPE,
            text=True,
        )
        return True
    except CalledProcessError:
        print(f"error executing {build_script}")
    except FileNotFoundError:
        print("could not execute script")
    return False


def export_topology_mermaid_mmd(
    graph: Graph, output: Path, config: MermaidStylingConfig | None = None
) -> None:
    with open(output, "w+") as f:
        f.write(create_topology_mermaid_mmd(graph, config))


def export_topology_mermaid_svg(
    graph: Graph, output: Path, config: MermaidStylingConfig | None = None
) -> None:
    _check_mmdc_on_path()

    mermaid: str = create_topology_mermaid_mmd(graph, config)

    with NamedTemporaryFile(delete=False, mode="w+", suffix=".mmd") as f:
        f.write(mermaid)
        source: Path = Path(f.name)

    build_script: Path = _create_mmdc_script(
        create_mmdc_script_content(source=source, output=output)
    )

    if _execute_build_script(build_script):
        build_script.unlink()
        source.unlink()


@cache
def _write_mermaid_config() -> Path:
    with NamedTemporaryFile(delete=False, mode="w+", suffix=".json") as f:
        f.write(_MERMAID_CONFIG_JSON)

        path: Path = Path(f.name)
        on_script_exit(path.unlink)
        return path


@cache
def _write_puppeteer_config() -> Path:
    with NamedTemporaryFile(delete=False, mode="w+", suffix=".json") as f:
        f.write(_PUPPETEER_CONFIG_JSON)

        path: Path = Path(f.name)
        on_script_exit(path.unlink)
        return path
