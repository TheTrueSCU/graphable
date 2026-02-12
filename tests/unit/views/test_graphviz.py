from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, mock_open, patch

from pytest import fixture, raises

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.graphviz import (
    GraphvizStylingConfig,
    _check_dot_on_path,
    create_topology_graphviz_dot,
    export_topology_graphviz_dot,
    export_topology_graphviz_svg,
)


class TestGraphviz:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_graphviz_dot_default(self, graph_fixture):
        g, a, b = graph_fixture
        dot = create_topology_graphviz_dot(g)

        assert "digraph G {" in dot
        assert '"A" [label="A"]' in dot
        assert '"B" [label="B"]' in dot
        assert '"A" -> "B"' in dot

    def test_create_topology_graphviz_dot_custom_config(self, graph_fixture):
        g, a, b = graph_fixture

        config = GraphvizStylingConfig(
            node_label_fnc=lambda n: f"Node:{n.reference}",
            node_attr_fnc=lambda n: {"style": "filled", "fillcolor": "red"}
            if n.reference == "A"
            else {},
            edge_attr_fnc=lambda n, sn: {"label": "depends"},
            graph_attr={"rankdir": "LR"},
            node_attr_default={"shape": "box"},
            edge_attr_default={"color": "blue"},
        )

        dot = create_topology_graphviz_dot(g, config)

        assert 'rankdir="LR";' in dot
        assert 'node [shape="box"];' in dot
        assert 'edge [color="blue"];' in dot
        assert '"A" [label="Node:A", style="filled", fillcolor="red"]' in dot
        assert '"A" -> "B" [label="depends"]' in dot

    def test_export_topology_graphviz_dot(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.dot")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_graphviz_dot(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()

    @patch("graphable.views.graphviz.which")
    def test_check_dot_on_path_success(self, mock_which):
        mock_which.return_value = "/usr/bin/dot"
        _check_dot_on_path()  # Should not raise

    @patch("graphable.views.graphviz.which")
    def test_check_dot_on_path_failure(self, mock_which):
        mock_which.return_value = None
        with raises(FileNotFoundError):
            _check_dot_on_path()

    @patch("graphable.views.graphviz.run")
    @patch("graphable.views.graphviz._check_dot_on_path")
    def test_export_topology_graphviz_svg_success(
        self, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.return_value = MagicMock()

        export_topology_graphviz_svg(g, output_path)

        mock_check.assert_called_once()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "dot" in args[0]
        assert "-Tsvg" in args[0]
        assert str(output_path) in args[0]

    @patch("graphable.views.graphviz.run")
    @patch("graphable.views.graphviz._check_dot_on_path")
    def test_export_topology_graphviz_svg_failure(
        self, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.side_effect = CalledProcessError(1, "dot", stderr="error")

        with raises(CalledProcessError):
            export_topology_graphviz_svg(g, output_path)

    @patch("graphable.views.graphviz.run")
    @patch("graphable.views.graphviz._check_dot_on_path")
    def test_export_topology_graphviz_svg_generic_exception(
        self, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.side_effect = Exception("generic error")

        with raises(Exception):
            export_topology_graphviz_svg(g, output_path)

    def test_create_topology_graphviz_dot_clustering(self):
        a = Graphable("A")
        a.add_tag("group1")
        b = Graphable("B")
        b.add_tag("group1")
        c = Graphable("C")
        c.add_tag("group2")

        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        from graphable.views.graphviz import GraphvizStylingConfig

        config = GraphvizStylingConfig(cluster_by_tag=True)

        dot = create_topology_graphviz_dot(g, config)

        assert 'subgraph "cluster_group1"' in dot
        assert 'label="group1";' in dot
        assert 'subgraph "cluster_group2"' in dot
        assert 'label="group2";' in dot
        assert '"A" [label="A"];' in dot
        assert '"B" [label="B"];' in dot
        assert '"C" [label="C"];' in dot
        assert '"A" -> "B"' in dot
        assert '"B" -> "C"' in dot
