import json
from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.cytoscape import (
    CytoscapeStylingConfig,
    create_topology_cytoscape,
    export_topology_cytoscape,
)


class TestCytoscape:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_cytoscape_default(self, graph_fixture):
        g, a, b = graph_fixture
        json_str = create_topology_cytoscape(g)
        elements = json.loads(json_str)

        assert len(elements) == 3  # A, B, edge A_B

        # Verify node
        node_a = next(e for e in elements if e["data"].get("id") == "A")
        assert node_a["data"]["label"] == "A"

        # Verify edge
        edge = next(e for e in elements if "source" in e["data"])
        assert edge["data"]["source"] == "A"
        assert edge["data"]["target"] == "B"

    def test_create_topology_cytoscape_custom_data(self, graph_fixture):
        g, a, b = graph_fixture
        config = CytoscapeStylingConfig(node_data_fnc=lambda n: {"extra": True})
        json_str = create_topology_cytoscape(g, config=config)
        data = json.loads(json_str)

        for element in data:
            if "source" not in element["data"]:  # It's a node
                assert element["data"]["extra"] is True

    def test_create_topology_cytoscape_edge_data(self, graph_fixture):
        g, a, b = graph_fixture
        config = CytoscapeStylingConfig(edge_data_fnc=lambda n, sn: {"weight": 10})
        json_str = create_topology_cytoscape(g, config=config)
        data = json.loads(json_str)

        edge = next(e for e in data if "source" in e["data"])
        assert edge["data"]["weight"] == 10

    def test_export_topology_cytoscape(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.json")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_cytoscape(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
