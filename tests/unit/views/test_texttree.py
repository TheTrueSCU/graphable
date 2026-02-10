from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.texttree import (
    TextTreeStylingConfig,
    create_topology_tree_txt,
    export_topology_tree_txt,
)


class TestTextTree:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        g = Graph()
        # C depends on B, B depends on A
        # A -> B -> C
        g.add_edge(a, b)
        g.add_edge(b, c)
        return g, a, b, c

    def test_create_topology_tree_txt_simple(self, graph_fixture):
        g, a, b, c = graph_fixture
        # C is the sink
        tree = create_topology_tree_txt(g)

        # Expected:
        # C
        # └─ B
        #    └─ A

        assert "C" in tree
        assert "└─ B" in tree
        assert "   └─ A" in tree

    def test_create_topology_tree_txt_custom_config(self, graph_fixture):
        g, a, b, c = graph_fixture
        config = TextTreeStylingConfig(
            initial_indent="  ", node_text_fnc=lambda n: f"[{n.reference}]"
        )
        tree = create_topology_tree_txt(g, config)

        assert "  [C]" in tree
        assert "  └─ [B]" in tree
        assert "     └─ [A]" in tree

    def test_create_topology_tree_txt_circular_or_revisited(self):
        # E -> A, A -> B, A -> C, B -> D, C -> D
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        d = Graphable("D")
        e = Graphable("E")

        g = Graph()
        g.add_edge(e, a)
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)

        tree = create_topology_tree_txt(g)

        assert "D" in tree
        assert "A" in tree
        assert "B" in tree
        assert "C" in tree
        assert "E" in tree
        assert "└─ E" in tree
        assert "(see above)" in tree

    def test_export_topology_tree_txt(self, graph_fixture):
        g, _, _, _ = graph_fixture
        output_path = Path("output.txt")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_tree_txt(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
