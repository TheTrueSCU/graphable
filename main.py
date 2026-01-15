from emoji import emojize
from pathlib import Path
from rich.console import Console

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.mermaid import MermaidStylingConfig, export_topology_mermaid_svg
from graphable.views.texttree import TextTreeStylingConfig, create_topology_tree_txt


class Node(Graphable[str, "Node"]):
    def __init__(self, name: str, special: bool = False):
        super().__init__(name)
        self._special = special

    @property
    def special(self) -> bool:
        return self._special


def main():
    console = Console()

    a: Node = Node("a")
    b: Node = Node("b", special=True)
    c: Node = Node("c")
    d: Node = Node("d", special=True)
    e: Node = Node("e")
    f: Node = Node("f")
    g: Node = Node("g", special=True)
    h: Node = Node("h")
    i: Node = Node("i")
    j: Node = Node("j")
    k: Node = Node("k", special=True)
    l: Node = Node("l")

    a._add_dependent(b)
    b._add_depends_on(a)
    b._add_dependent(c)
    c._add_depends_on(b)
    c._add_dependent(i)
    i._add_depends_on(c)
    d._add_dependent(e)
    e._add_depends_on(d)
    e._add_dependent(i)
    i._add_depends_on(e)
    d._add_dependent(f)
    f._add_depends_on(d)
    f._add_dependent(i)
    i._add_depends_on(f)
    g._add_dependent(h)
    h._add_depends_on(g)
    g._add_dependent(i)
    i._add_depends_on(g)
    h._add_dependent(i)
    i._add_depends_on(h)
    i._add_dependent(j)
    j._add_depends_on(i)

    k._add_dependent(l)
    l._add_depends_on(k)

    nodes: set[Node] = {a, b, c, d, e, f, g, h, i, j, k, l}

    graph: Graph[Node] = Graph(nodes)
    console.print([node.reference for node in graph.topological_order()])
    console.print(
        [
            node.reference
            for node in graph.filtered_topological_order(lambda x: x.special)
        ]
    )

    console.print([node.reference for node in graph.sources])
    console.print([node.reference for node in graph.sinks])

    subgraph: Graph[Node] = graph.subgraph(set([e]))
    console.print([node.reference for node in subgraph.topological_order()])
    console.print(
        [
            node.reference
            for node in subgraph.filtered_topological_order(lambda x: x.special)
        ]
    )

    console.print([node.reference for node in subgraph.sources])
    console.print([node.reference for node in subgraph.sinks])

    def txt_node_text_fnc(node: Node) -> str:
        if node.special:
            return emojize(f':green_circle: {node.reference}')
        return emojize(f':red_square: {node.reference}')

    txt_config: TextTreeStylingConfig = TextTreeStylingConfig(
        node_text_fnc = txt_node_text_fnc
    )

    console.print(create_topology_tree_txt(graph, txt_config))

    def mmd_node_style_fnc(node: Node) -> str:
        if node.special:
            return "fill:#EEEE90"
        return ""

    mmd_config: MermaidStylingConfig = MermaidStylingConfig(
        node_style_fnc = mmd_node_style_fnc
    )

    export_topology_mermaid_svg(graph, Path(r"blah.svg"), mmd_config)


if __name__ == "__main__":
    main()
