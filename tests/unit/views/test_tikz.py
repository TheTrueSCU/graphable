from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.tikz import (
    TikzStylingConfig,
    create_topology_tikz,
    export_topology_tikz,
)


class TestTikZ:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_tikz_graphs_lib(self, graph_fixture):
        g, a, b = graph_fixture
        tikz = create_topology_tikz(g)

        assert r"\begin{tikzpicture}" in tikz
        assert r"\usetikzlibrary{graphs}" in tikz
        assert f"node_{id(a)} -> node_{id(b)}" in tikz
        assert r"\end{tikzpicture}" in tikz

    def test_create_topology_tikz_standard(self, graph_fixture):
        g, a, b = graph_fixture
        config = TikzStylingConfig(use_graphs_lib=False)
        tikz = create_topology_tikz(g, config)

        assert r"\node" in tikz
        assert r"\draw" in tikz
        assert "node_" in tikz
        assert r"\end{tikzpicture}" in tikz

    def test_export_topology_tikz(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.tex")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_tikz(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
