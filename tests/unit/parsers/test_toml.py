from graphable.graph import Graph, Graphable
from graphable.parsers.toml import load_graph_toml
from graphable.views.toml import create_topology_toml


def test_load_graph_toml_roundtrip():
    # A -> B
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    toml_str = create_topology_toml(g)

    loaded_g = load_graph_toml(toml_str)

    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert "B" in loaded_g
    assert loaded_g["A"].is_tagged("t1")
    assert loaded_g["B"] in loaded_g["A"].dependents


def test_load_graph_toml_from_file(tmp_path):
    output_file = tmp_path / "graph.toml"
    content = """
[[nodes]]
id = "A"
reference = "A"
tags = ["important"]

[[edges]]
source = "A"
target = "B"

[[nodes]]
id = "B"
reference = "B"
tags = []
"""
    output_file.write_text(content)

    loaded_g = load_graph_toml(output_file)
    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert "B" in loaded_g
    assert loaded_g["A"].is_tagged("important")
    assert loaded_g["B"] in loaded_g["A"].dependents
