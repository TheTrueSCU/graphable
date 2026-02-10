from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.html import (
    HtmlStylingConfig,
    create_topology_html,
    export_topology_html,
)


class TestHtml:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_html_default(self, graph_fixture):
        g, a, b = graph_fixture
        html = create_topology_html(g)

        assert "<!DOCTYPE html>" in html
        assert "cytoscape.min.js" in html
        assert "Graphable Visualization" in html
        assert '"source": "A"' in html
        assert '"target": "B"' in html

    def test_create_topology_html_custom_config(self, graph_fixture):
        g, a, b = graph_fixture
        config = HtmlStylingConfig(title="My Graph", theme="dark", node_color="red")
        html = create_topology_html(g, config)

        assert "<title>My Graph</title>" in html
        assert "background-color: #222" in html
        assert "'background-color': 'red'" in html

    def test_export_topology_html(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.html")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_html(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()
