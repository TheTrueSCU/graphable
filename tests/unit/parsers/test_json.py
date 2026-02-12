import json

from graphable.graph import Graph, Graphable
from graphable.parsers.json import load_graph_json
from graphable.views.json import create_topology_json


def test_load_graph_json_roundtrip():
    # A -> B
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    json_str = create_topology_json(g)

    loaded_g = load_graph_json(json_str)

    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert "B" in loaded_g
    assert loaded_g["A"].is_tagged("t1")
    assert loaded_g["B"] in loaded_g["A"].dependents


def test_load_graph_json_orphaned_nodes():
    data = {
        "nodes": [
            {"id": "A", "reference": "A", "tags": []},
            {"id": "B", "reference": "B", "tags": []},
        ],
        "edges": [],
    }
    json_str = json.dumps(data)

    loaded_g = load_graph_json(json_str)
    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert "B" in loaded_g


def test_load_graph_json_from_file(tmp_path):
    output_file = tmp_path / "graph.json"
    data = {"nodes": [{"id": "A", "reference": "A", "tags": []}], "edges": []}
    output_file.write_text(json.dumps(data))

    loaded_g = load_graph_json(output_file)
    assert len(loaded_g) == 1
    assert "A" in loaded_g
