from pathlib import Path
from unittest.mock import MagicMock, patch

from graphable.cli.commands.core import info_command, load_graph, paths_command
from graphable.graph import Graph
from graphable.graphable import Graphable


def test_load_graph_slicing():
    a = Graphable("A")
    b = Graphable("B")
    c = Graphable("C")
    g = Graph()
    g.add_edge(a, b)
    g.add_edge(b, c)

    with patch("graphable.cli.commands.core.get_parser") as mock_get_parser:
        mock_parser = MagicMock(return_value=g)
        mock_get_parser.return_value = mock_parser

        # Upstream of B should be {A, B}
        g_up = load_graph(Path("test.json"), upstream_of="B")
        assert len(g_up) == 2
        assert "A" in g_up
        assert "B" in g_up
        assert "C" not in g_up

        # Downstream of B should be {B, C}
        g_down = load_graph(Path("test.json"), downstream_of="B")
        assert len(g_down) == 2
        assert "B" in g_down
        assert "C" in g_down
        assert "A" not in g_down


def test_paths_command(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text(
        '{"nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}], "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}]}'
    )

    paths = paths_command(graph_file, "A", "C")
    assert paths == [["A", "B", "C"]]


def test_info_command_slicing(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text(
        '{"nodes": [{"id": "A"}, {"id": "B"}], "edges": [{"source": "A", "target": "B"}]}'
    )

    # Full graph
    data = info_command(graph_file)
    assert data["nodes"] == 2

    # Sliced graph (upstream of A is just A)
    data_sliced = info_command(graph_file, upstream_of="A")
    assert data_sliced["nodes"] == 1
    assert data_sliced["sources"] == ["A"]
