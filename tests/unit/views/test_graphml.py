from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.graphml import (
    GraphmlStylingConfig,
    create_topology_graphml,
    export_topology_graphml,
)


class TestGraphML:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        a.add_tag("source")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_graphml_default(self, graph_fixture):
        g, a, b = graph_fixture
        graphml = create_topology_graphml(g)

        assert 'xmlns="http://graphml.graphdrawing.org/xmlns"' in graphml
        assert '<node id="A">' in graphml
        assert '<node id="B"/>' in graphml
        assert '<edge id="e_A_B" source="A" target="B"/>' in graphml
        assert '<data key="tags">source</data>' in graphml

    def test_create_topology_graphml_custom_config(self, graph_fixture):
        g, a, b = graph_fixture
        config = GraphmlStylingConfig(node_ref_fnc=lambda n: f"id_{n.reference}")
        graphml = create_topology_graphml(g, config)

        assert '<node id="id_A">' in graphml
        assert '<edge id="e_id_A_id_B" source="id_A" target="id_B"/>' in graphml

    def test_export_topology_graphml(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.graphml")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_graphml(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
