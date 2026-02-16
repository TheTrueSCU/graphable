from json import loads
from pathlib import Path
from unittest.mock import MagicMock, patch

from pytest import raises

from graphable.cli.commands.core import (
    check_command,
    checksum_command,
    convert_command,
    diff_command,
    diff_visual_command,
    info_command,
    reduce_command,
    render_command,
    verify_command,
    write_checksum_command,
)
from graphable.enums import Engine


def test_info_command(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text(
        '{"nodes": [{"id": "A"}, {"id": "B"}], "edges": [{"source": "A", "target": "B"}]}'
    )

    data = info_command(graph_file)
    assert data["nodes"] == 2
    assert data["edges"] == 1
    assert "A" in data["sources"]
    assert "B" in data["sinks"]


def test_check_command(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text('{"nodes": [{"id": "A"}], "edges": []}')

    data = check_command(graph_file)
    assert data["valid"] is True

    # Cyclic graph
    cyclic_file = tmp_path / "cyclic.json"
    cyclic_file.write_text(
        '{"nodes": [{"id": "A"}, {"id": "B"}], "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}]}'
    )
    data = check_command(cyclic_file)
    assert data["valid"] is False
    assert "Cycle detected" in data["error"] or "would create a cycle" in data["error"]


def test_convert_command(tmp_path):
    input_file = tmp_path / "test.json"
    input_file.write_text('{"nodes": [{"id": "A"}], "edges": []}')
    output_file = tmp_path / "test.yaml"

    convert_command(input_file, output_file)
    assert output_file.exists()
    assert "id: A" in output_file.read_text()


def test_convert_command_error_on_images(tmp_path):
    input_file = tmp_path / "test.json"
    input_file.write_text('{"nodes": [{"id": "A"}], "edges": []}')

    with raises(ValueError, match="is for images. Use the 'render' command instead"):
        convert_command(input_file, Path("output.png"))

    with raises(ValueError, match="is for images. Use the 'render' command instead"):
        convert_command(input_file, Path("output.svg"))


def test_reduce_command(tmp_path):
    input_file = tmp_path / "test.json"
    # A -> B -> C, A -> C
    input_file.write_text(
        '{"nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}], "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "A", "target": "C"}]}'
    )
    output_file = tmp_path / "reduced.json"

    reduce_command(input_file, output_file)
    assert output_file.exists()

    data = loads(output_file.read_text())
    # Should have 2 edges (A->B, B->C) instead of 3
    assert len(data["edges"]) == 2


def test_checksum_command(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text('{"nodes": [{"id": "A"}], "edges": []}')

    from graphable.graph import Graph

    g = Graph.from_json(graph_file)
    expected = g.checksum()

    assert checksum_command(graph_file) == expected


def test_write_checksum_command(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text('{"nodes": [{"id": "A"}], "edges": []}')
    checksum_file = tmp_path / "test.blake2b"

    write_checksum_command(graph_file, checksum_file)
    assert checksum_file.exists()

    from graphable.graph import Graph

    g = Graph.from_json(graph_file)
    assert checksum_file.read_text() == g.checksum()


def test_verify_command(tmp_path):
    graph_file = tmp_path / "test.json"
    graph_file.write_text('{"nodes": [{"id": "A"}], "edges": []}')

    from graphable.graph import Graph

    g = Graph.from_json(graph_file)
    digest = g.checksum()

    # Explicit expected
    assert verify_command(graph_file, digest)["valid"] is True
    assert verify_command(graph_file, "wrong")["valid"] is False

    # Embedded checksum
    embedded_file = tmp_path / "embedded.yaml"
    g.write(embedded_file, embed_checksum=True)

    data = verify_command(embedded_file)
    assert data["valid"] is True
    assert data["actual"] == digest
    assert data["expected"] == digest


def test_diff_command(tmp_path):
    f1 = tmp_path / "v1.json"
    f1.write_text('{"nodes": [{"id": "A"}], "edges": []}')
    f2 = tmp_path / "v2.json"
    f2.write_text('{"nodes": [{"id": "A"}, {"id": "B"}], "edges": []}')

    diff = diff_command(f1, f2)
    assert "B" in diff["added_nodes"]


def test_diff_visual_command(tmp_path):
    f1 = tmp_path / "v1.json"
    f1.write_text('{"nodes": [{"id": "A"}], "edges": []}')
    f2 = tmp_path / "v2.json"
    f2.write_text('{"nodes": [{"id": "A"}, {"id": "B"}], "edges": []}')
    output = tmp_path / "diff.json"

    diff_visual_command(f1, f2, output)
    assert output.exists()
    assert "diff:added" in output.read_text()


@patch("graphable.cli.commands.core.load_graph")
def test_render_command_explicit_engine(mock_load_graph):
    """Verify render_command calls the correct engine when explicitly provided."""
    mock_g = MagicMock()
    mock_load_graph.return_value = mock_g

    input_path = Path("input.json")
    output_path = Path("output.png")

    # Mermaid
    with patch("graphable.views.mermaid.export_topology_mermaid_image") as mock_mermaid:
        render_command(input_path, output_path, engine=Engine.MERMAID)
        mock_mermaid.assert_called_once_with(mock_g, output_path)

    # Graphviz
    with patch(
        "graphable.views.graphviz.export_topology_graphviz_image"
    ) as mock_graphviz:
        render_command(input_path, output_path, engine=Engine.GRAPHVIZ)
        mock_graphviz.assert_called_once_with(mock_g, output_path)

    # D2
    with patch("graphable.views.d2.export_topology_d2_image") as mock_d2:
        render_command(input_path, output_path, engine=Engine.D2)
        mock_d2.assert_called_once_with(mock_g, output_path)

    # PlantUML
    with patch("graphable.views.plantuml.export_topology_plantuml_image") as mock_puml:
        render_command(input_path, output_path, engine=Engine.PLANTUML)
        mock_puml.assert_called_once_with(mock_g, output_path)


@patch("graphable.cli.commands.core.load_graph")
@patch("graphable.views.utils.detect_engine")
def test_render_command_auto_detection(mock_detect_engine, mock_load_graph):
    """Verify render_command auto-detects engine when not provided."""
    mock_g = MagicMock()
    mock_load_graph.return_value = mock_g
    mock_detect_engine.return_value = "graphviz"

    input_path = Path("input.json")
    output_path = Path("output.png")

    with patch(
        "graphable.views.graphviz.export_topology_graphviz_image"
    ) as mock_graphviz:
        render_command(input_path, output_path)
        mock_detect_engine.assert_called_once()
        mock_graphviz.assert_called_once_with(mock_g, output_path)


@patch("graphable.cli.commands.core.load_graph")
def test_render_command_invalid_engine(mock_load_graph):
    """Verify render_command raises ValueError for unknown engine."""
    mock_load_graph.return_value = MagicMock()
    with raises(ValueError, match="Unknown rendering engine: unknown"):
        render_command(Path("i.json"), Path("o.png"), engine="unknown")
