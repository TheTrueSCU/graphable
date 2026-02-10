from pathlib import Path
from unittest.mock import mock_open, patch

from pytest import fixture

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.csv import create_topology_csv, export_topology_csv


class TestCSV:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_csv_default(self, graph_fixture):
        g, a, b = graph_fixture
        csv_str = create_topology_csv(g)

        assert "source,target" in csv_str
        assert "A,B" in csv_str

    def test_create_topology_csv_no_header(self, graph_fixture):
        g, a, b = graph_fixture
        csv_str = create_topology_csv(g, include_header=False)

        assert "source,target" not in csv_str
        assert "A,B" in csv_str

    def test_export_topology_csv(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.csv")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_csv(g, output_path)

            mock_file.assert_called_with(output_path, "w+", newline="")
            mock_file().write.assert_called()
