from graphable.graph import Graph, Graphable
from graphable.parsers.graphml import load_graph_graphml
from graphable.views.graphml import create_topology_graphml


def test_load_graph_graphml_roundtrip():
    # A -> B
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    graphml_str = create_topology_graphml(g)

    loaded_g = load_graph_graphml(graphml_str)

    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert "B" in loaded_g
    assert loaded_g["A"].is_tagged("t1")
    assert loaded_g["B"] in loaded_g["A"].dependents


def test_load_graph_graphml_from_file(tmp_path):
    output_file = tmp_path / "graph.graphml"
    content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="reference" for="node" attr.name="reference" attr.type="string"/>
  <key id="tags" for="node" attr.name="tags" attr.type="string"/>
  <graph id="G" edgedefault="directed">
    <node id="A">
      <data key="reference">A</data>
      <data key="tags">important,new</data>
    </node>
    <node id="B"/>
    <edge source="A" target="B"/>
  </graph>
</graphml>
"""
    output_file.write_text(content)

    loaded_g = load_graph_graphml(output_file)
    assert len(loaded_g) == 2
    assert "A" in loaded_g
    assert loaded_g["A"].is_tagged("important")
    assert loaded_g["A"].is_tagged("new")
    assert loaded_g["B"] in loaded_g["A"].dependents
