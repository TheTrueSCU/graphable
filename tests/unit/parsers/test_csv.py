from graphable.graph import Graph, Graphable
from graphable.parsers.csv import load_graph_csv
from graphable.views.csv import create_topology_csv


def test_load_graph_csv_roundtrip():
    # A -> B, B -> C
    a = Graphable("A")
    b = Graphable("B")
    c = Graphable("C")
    g = Graph()
    g.add_edge(a, b)
    g.add_edge(b, c)

    csv_str = create_topology_csv(g)

    loaded_g = load_graph_csv(csv_str)

    assert len(loaded_g) == 3
    assert "A" in loaded_g
    assert "B" in loaded_g
    assert "C" in loaded_g
    assert loaded_g["B"] in loaded_g["A"].dependents
    assert loaded_g["C"] in loaded_g["B"].dependents


def test_load_graph_csv_with_header():
    content = """source,target
A,B
B,C
"""
    loaded_g = load_graph_csv(content)
    assert len(loaded_g) == 3
    assert "A" in loaded_g
    assert "C" in loaded_g


def test_load_graph_csv_from_file(tmp_path):
    output_file = tmp_path / "graph.csv"
    output_file.write_text("A,B\nC,D")

    loaded_g = load_graph_csv(output_file)
    assert len(loaded_g) == 4
    assert "A" in loaded_g
    assert loaded_g["B"] in loaded_g["A"].dependents
