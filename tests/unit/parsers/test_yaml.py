from graphable.graph import Graph, Graphable
from graphable.parsers.yaml import load_graph_yaml
from graphable.views.yaml import create_topology_yaml


def test_load_graph_yaml_roundtrip():
    # A -> B
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    yaml_str = create_topology_yaml(g)

    loaded_g = load_graph_yaml(yaml_str)

    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert "B" in loaded_g
    assert loaded_g["A"].is_tagged("t1")
    assert loaded_g["B"] in loaded_g["A"].dependents


def test_load_graph_yaml_from_file(tmp_path):
    output_file = tmp_path / "graph.yaml"
    content = """
nodes:
  - id: A
    reference: A
    tags: ["important"]
edges: []
"""
    output_file.write_text(content)

    loaded_g = load_graph_yaml(output_file)
    assert len(loaded_g) == 1
    assert "A" in loaded_g
    assert loaded_g["A"].is_tagged("important")


def test_load_graph_yaml_wrapped():
    yaml_data = """
graph:
  nodes:
    - id: A
    - id: B
  edges:
    - source: A
      target: B
"""
    g = load_graph_yaml(yaml_data)
    assert len(g) == 2
    assert "A" in g
    assert "B" in g
