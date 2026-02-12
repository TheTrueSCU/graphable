from graphable.graph import Graph, Graphable
from graphable.parsers.json import load_graph_json
from graphable.views.csv import create_topology_csv
from graphable.views.graphml import create_topology_graphml
from graphable.views.json import create_topology_json
from graphable.views.toml import create_topology_toml
from graphable.views.yaml import create_topology_yaml


def test_graph_roundtrip_json():
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    json_data = create_topology_json(g)
    g_parsed = Graph.from_json(json_data)

    assert g == g_parsed


def test_graph_roundtrip_yaml():
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    yaml_data = create_topology_yaml(g)
    g_parsed = Graph.from_yaml(yaml_data)

    assert g == g_parsed


def test_graph_roundtrip_toml():
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    toml_data = create_topology_toml(g)
    g_parsed = Graph.from_toml(toml_data)

    assert g == g_parsed


def test_graph_roundtrip_csv():
    # CSV only preserves structure, not tags
    a = Graphable("A")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    csv_data = create_topology_csv(g)
    g_parsed = Graph.from_csv(csv_data)

    # We can't use g == g_parsed because g has tags (empty) and parsed might differ
    # if implementation details change, but actually CSV graph is simpler.
    # Let's ensure they are equal in structure.
    assert len(g) == len(g_parsed)
    assert "A" in g_parsed
    assert "B" in g_parsed
    assert g_parsed["B"] in g_parsed["A"].dependents


def test_graph_roundtrip_graphml():
    a = Graphable("A")
    a.add_tag("t1")
    b = Graphable("B")
    g = Graph()
    g.add_edge(a, b)

    graphml_data = create_topology_graphml(g)
    g_parsed = Graph.from_graphml(graphml_data)

    assert g == g_parsed


def test_graph_parse_generic():
    data = '{"nodes": [{"id": "A"}], "edges": []}'
    g = Graph.parse(load_graph_json, data)
    assert len(g) == 1
    assert "A" in g


def test_graph_from_json():
    data = '{"nodes": [{"id": "A"}], "edges": []}'
    g = Graph.from_json(data)
    assert len(g) == 1
    assert "A" in g


def test_graph_from_yaml():
    data = "nodes: [{id: A}]"
    g = Graph.from_yaml(data)
    assert len(g) == 1
    assert "A" in g


def test_graph_from_toml():
    data = """
[[nodes]]
id = "A"
"""
    g = Graph.from_toml(data)
    assert len(g) == 1
    assert "A" in g


def test_graph_from_csv():
    data = "A,B"
    g = Graph.from_csv(data)
    assert len(g) == 2
    assert "A" in g
    assert "B" in g


def test_graph_from_graphml():
    data = '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"><graph id="G"><node id="A"/></graph></graphml>'
    g = Graph.from_graphml(data)
    assert len(g) == 1
    assert "A" in g
