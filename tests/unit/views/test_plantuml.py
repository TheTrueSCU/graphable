from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, mock_open, patch

from pytest import fixture, raises

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.plantuml import (
    PlantUmlStylingConfig,
    _check_plantuml_on_path,
    create_topology_plantuml,
    export_topology_plantuml,
    export_topology_plantuml_svg,
)


class TestPlantUML:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_plantuml_default(self, graph_fixture):
        g, a, b = graph_fixture
        puml = create_topology_plantuml(g)

        assert "@startuml" in puml
        assert 'node "A" as' in puml
        assert 'node "B" as' in puml
        assert "-->" in puml
        assert "@enduml" in puml

    def test_create_topology_plantuml_custom_config(self, graph_fixture):
        g, a, b = graph_fixture
        config = PlantUmlStylingConfig(
            node_ref_fnc=lambda n: n.reference,
            node_type="component",
            direction="left to right direction",
        )
        puml = create_topology_plantuml(g, config)

        assert "left to right" in puml
        assert 'component "A" as A' in puml
        assert "A --> B" in puml

    def test_export_topology_plantuml(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.puml")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_plantuml(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()

    @patch("graphable.views.plantuml.which")
    def test_check_plantuml_on_path_success(self, mock_which):
        mock_which.return_value = "/usr/bin/plantuml"
        _check_plantuml_on_path()  # Should not raise

    @patch("graphable.views.plantuml.which")
    def test_check_plantuml_on_path_failure(self, mock_which):
        mock_which.return_value = None
        with raises(FileNotFoundError):
            _check_plantuml_on_path()

    @patch("graphable.views.plantuml.run")
    @patch("graphable.views.plantuml._check_plantuml_on_path")
    @patch("builtins.open", new_callable=mock_open)
    def test_export_topology_plantuml_svg_success(
        self, mock_file, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.return_value = MagicMock()

        export_topology_plantuml_svg(g, output_path)

        mock_check.assert_called_once()
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "plantuml" in args[0]
        assert "-tsvg" in args[0]

    @patch("graphable.views.plantuml.run")
    @patch("graphable.views.plantuml._check_plantuml_on_path")
    @patch("builtins.open", new_callable=mock_open)
    def test_export_topology_plantuml_svg_failure(
        self, mock_file, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.side_effect = CalledProcessError(1, "plantuml", stderr="error")

        with raises(CalledProcessError):
            export_topology_plantuml_svg(g, output_path)

    @patch("graphable.views.plantuml.run")
    @patch("graphable.views.plantuml._check_plantuml_on_path")
    @patch("builtins.open", new_callable=mock_open)
    def test_export_topology_plantuml_svg_generic_exception(
        self, mock_file, mock_check, mock_run, graph_fixture
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        mock_run.side_effect = Exception("generic error")

        with raises(Exception):
            export_topology_plantuml_svg(g, output_path)

    def test_create_topology_plantuml_clustering(self):
        a = Graphable("A")
        a.add_tag("group1")
        b = Graphable("B")
        b.add_tag("group1")
        c = Graphable("C")
        c.add_tag("group2")

        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        from graphable.views.plantuml import PlantUmlStylingConfig

        config = PlantUmlStylingConfig(
            cluster_by_tag=True, node_ref_fnc=lambda n: n.reference
        )

        puml = create_topology_plantuml(g, config)

        assert 'package "group1" {' in puml
        assert 'package "group2" {' in puml
        assert 'node "A" as A' in puml
        assert 'node "B" as B' in puml
        assert 'node "C" as C' in puml
        assert "A --> B" in puml
        assert "B --> C" in puml
