from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture
from yaml import safe_load

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.yaml import (
    YamlStylingConfig,
    create_topology_yaml,
    export_topology_yaml,
)


class TestYAML:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        a.add_tag("tag1")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_yaml_default(self, graph_fixture):
        g, a, b = graph_fixture
        yaml_str = create_topology_yaml(g)
        data = safe_load(yaml_str)

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

        node_a = next(n for n in data["nodes"] if n["id"] == "A")
        assert node_a["tags"] == ["tag1"]

        edge = data["edges"][0]
        assert edge["source"] == "A"
        assert edge["target"] == "B"

    def test_create_topology_yaml_custom_data(self, graph_fixture):
        g, a, b = graph_fixture
        config = YamlStylingConfig(node_data_fnc=lambda n: {"extra": True})
        yaml_str = create_topology_yaml(g, config=config)
        data = safe_load(yaml_str)

        for node in data["nodes"]:
            assert node["extra"] is True

    def test_export_topology_yaml(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.yaml")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_yaml(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
