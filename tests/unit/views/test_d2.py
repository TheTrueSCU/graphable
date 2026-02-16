from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, mock_open, patch

from pytest import fixture, raises

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.d2 import (
    D2StylingConfig,
    _check_d2_on_path,
    create_topology_d2,
    export_topology_d2,
    export_topology_d2_image,
)


class TestD2:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_d2_default(self, graph_fixture):
        g, a, b = graph_fixture
        d2 = create_topology_d2(g)

        assert "A: A" in d2
        assert "B: B" in d2
        assert "A -> B" in d2

    def test_create_topology_d2_custom_config(self, graph_fixture):
        g, a, b = graph_fixture

        config = D2StylingConfig(
            node_label_fnc=lambda n: f"Node:{n.reference}",
            node_style_fnc=lambda n: {"fill": "red"} if n.reference == "A" else {},
            edge_style_fnc=lambda n, sn: {"stroke": "blue"},
            layout="dagre",
            theme="200",
        )

        d2 = create_topology_d2(g, config)

        assert "layout-engine: dagre" in d2
        assert "A: Node:A" in d2
        assert "fill: red" in d2
        assert "A -> B: {" in d2
        assert "stroke: blue" in d2

    def test_create_topology_d2_edge_style_empty(self, graph_fixture):
        g, a, b = graph_fixture
        config = D2StylingConfig(edge_style_fnc=lambda n, sn: {})
        d2 = create_topology_d2(g, config)
        assert "A -> B" in d2
        assert "{" not in d2

    def test_export_topology_d2(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.d2")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_d2(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()

    @patch("graphable.views.d2.which")
    def test_check_d2_on_path_success(self, mock_which):
        mock_which.return_value = "/usr/bin/d2"
        _check_d2_on_path()  # Should not raise

    @patch("graphable.views.d2.which")
    def test_check_d2_on_path_failure(self, mock_which):
        mock_which.return_value = None
        with raises(FileNotFoundError):
            _check_d2_on_path()

    @patch("graphable.views.d2.run")
    @patch("graphable.views.d2._check_d2_on_path")
    def test_export_topology_d2_image_svg_success(self, mock_check, mock_run, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.return_value = MagicMock()

        export_topology_d2_image(g, output_path)

        mock_check.assert_called_once()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "d2" == args[0][0]
        assert str(output_path) in args[0]

    @patch("graphable.views.d2.run")
    @patch("graphable.views.d2._check_d2_on_path")
    def test_export_topology_d2_image_png_success(self, mock_check, mock_run, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.png")

        mock_run.return_value = MagicMock()

        export_topology_d2_image(g, output_path)

        mock_check.assert_called_once()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "d2" == args[0][0]
        assert str(output_path) in args[0]

    @patch("graphable.views.d2.run")
    @patch("graphable.views.d2._check_d2_on_path")
    def test_export_topology_d2_image_with_config(
        self, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")
        config = D2StylingConfig(theme="200", layout="elk")

        mock_run.return_value = MagicMock()

        export_topology_d2_image(g, output_path, config)

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert "--theme" in cmd
        assert "200" in cmd
        assert "--layout" in cmd
        assert "elk" in cmd

    @patch("graphable.views.d2.run")
    @patch("graphable.views.d2._check_d2_on_path")
    def test_export_topology_d2_image_failure(self, mock_check, mock_run, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.side_effect = CalledProcessError(1, "d2", stderr="error")

        with raises(CalledProcessError):
            export_topology_d2_image(g, output_path)

    @patch("graphable.views.d2.run")
    @patch("graphable.views.d2._check_d2_on_path")
    def test_export_topology_d2_image_generic_exception(
        self, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.side_effect = Exception("generic error")

        with raises(Exception):
            export_topology_d2_image(g, output_path)

    def test_create_topology_d2_clustering(self):
        a = Graphable("A")
        a.add_tag("group1")
        b = Graphable("B")
        b.add_tag("group1")
        c = Graphable("C")
        c.add_tag("group2")

        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        from graphable.views.d2 import D2StylingConfig

        config = D2StylingConfig(cluster_by_tag=True)

        d2 = create_topology_d2(g, config)

        assert "group1: {" in d2
        assert "group2: {" in d2
        assert "A: A" in d2
        assert "B: B" in d2
        assert "C: C" in d2
        assert "A -> B" in d2
        assert "B -> C" in d2
