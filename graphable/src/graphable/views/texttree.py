from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..graph import Graph
from ..graphable import Graphable


@dataclass
class TextTreeStylingConfig:
    initial_indent: str = ""
    node_text_fnc: Callable[[Graphable], str] = lambda n: n.reference


def create_topology_tree_txt(
    graph: Graph, config: TextTreeStylingConfig | None = None
) -> str:
    if config is None:
        config = TextTreeStylingConfig()

    def create_topology_subtree_txt(
        node: Graphable,
        indent: str = "",
        is_last: bool = True,
        is_root: bool = True,
        visited: set[Graphable] | None = None,
    ) -> str:
        if visited is None:
            visited = set[Graphable]()
        already_seen: bool = node in visited

        subtree: list[str] = []
        if is_root:
            subtree.append(f"{indent}{config.node_text_fnc(node)}")

            next_indent: str = indent

        else:
            marker: str = "└─ " if is_last else "├─ "
            suffix: str = " (see above)" if already_seen and node.depends_on else ""
            subtree.append(f"{indent}{marker}{config.node_text_fnc(node)}{suffix}")

            next_indent: str = indent + ("   " if is_last else "│  ")

        if already_seen:
            return "\n".join(subtree)
        visited.add(node)

        for i, subnode in enumerate(node.depends_on, start=1):
            subtree.append(
                create_topology_subtree_txt(
                    node=subnode,
                    indent=next_indent,
                    is_last=(i == len(node.depends_on)),
                    is_root=False,
                    visited=visited,
                )
            )

        return "\n".join(subtree)

    tree: list[str] = []
    for node in graph.sinks:
        tree.append(
            create_topology_subtree_txt(
                node=node, indent=config.initial_indent, is_root=True
            )
        )
    return "\n".join(tree)


def export_topology_tree_txt(
    graph: Graph, output: Path, config: TextTreeStylingConfig | None = None
) -> None:
    with open(output, "w+") as f:
        f.write(create_topology_tree_txt(graph, config))
