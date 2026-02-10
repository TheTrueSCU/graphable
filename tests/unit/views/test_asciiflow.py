from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.asciiflow import (
    AsciiflowStylingConfig,
    create_topology_ascii_flow,
    export_topology_ascii_flow,
)


class TestAsciiFlow:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_ascii_flow_default(self, graph_fixture):
        g, a, b = graph_fixture
        flow = create_topology_ascii_flow(g)

        assert "+---+" in flow
        assert "| A |" in flow
        assert "  +--> B" in flow
        assert "| B |" in flow

    def test_create_topology_ascii_flow_with_tags(self, graph_fixture):
        g, a, b = graph_fixture
        a.add_tag("source")

        config = AsciiflowStylingConfig(show_tags=True)
        flow = create_topology_ascii_flow(g, config)

        assert "| A [source] |" in flow
        assert "+------------+" in flow

    def test_create_topology_ascii_flow_custom_text(self, graph_fixture):
        g, a, b = graph_fixture
        config = AsciiflowStylingConfig(node_text_fnc=lambda n: f"Node {n.reference}")
        flow = create_topology_ascii_flow(g, config)

        assert "| Node A |" in flow
        assert "  +--> Node B" in flow

    def test_create_topology_ascii_flow_multiple_dependents(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(a, c)

        flow = create_topology_ascii_flow(g)
        # Check for multiple arrows from A
        assert "  +--> B" in flow
        assert "  +--> C" in flow

    def test_export_topology_ascii_flow(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.txt")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_ascii_flow(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
