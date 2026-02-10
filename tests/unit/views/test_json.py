import json
from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.json import (
    JsonStylingConfig,
    create_topology_json,
    export_topology_json,
)


class TestJSON:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        a.add_tag("tag1")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_json_default(self, graph_fixture):
        g, a, b = graph_fixture
        json_str = create_topology_json(g)
        data = json.loads(json_str)

        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

        node_a = next(n for n in data["nodes"] if n["id"] == "A")
        assert node_a["tags"] == ["tag1"]

        edge = data["edges"][0]
        assert edge["source"] == "A"
        assert edge["target"] == "B"

    def test_create_topology_json_custom_data(self, graph_fixture):
        g, a, b = graph_fixture
        config = JsonStylingConfig(node_data_fnc=lambda n: {"extra": True})
        json_str = create_topology_json(g, config=config)
        data = json.loads(json_str)

        for node in data["nodes"]:
            assert node["extra"] is True

    def test_export_topology_json(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.json")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_json(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
