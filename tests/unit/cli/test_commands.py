from graphable.cli.commands.core import (
    check_command,
    convert_command,
    info_command,
    reduce_command,
)


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


def test_reduce_command(tmp_path):
    input_file = tmp_path / "test.json"
    # A -> B -> C, A -> C
    input_file.write_text(
        '{"nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}], "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "A", "target": "C"}]}'
    )
    output_file = tmp_path / "reduced.json"

    reduce_command(input_file, output_file)
    assert output_file.exists()

    import json

    data = json.loads(output_file.read_text())
    # Should have 2 edges (A->B, B->C) instead of 3
    assert len(data["edges"]) == 2
