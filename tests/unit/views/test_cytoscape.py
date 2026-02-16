import json

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.registry import EXPORTERS
from graphable.views.cytoscape import (
    CytoscapeStylingConfig,
    create_topology_cytoscape,
    export_topology_cytoscape,
)


def test_cytoscape_registration():
    """Verify that .cy.json is registered as an exporter."""
    assert ".cy.json" in EXPORTERS


def test_cytoscape_config_defaults():
    """Verify default configuration values for Cytoscape."""
    config = CytoscapeStylingConfig()
    assert config.node_data_fnc is None
    assert config.edge_data_fnc is None
    assert config.indent == 2

    node = Graphable("A")
    assert config.reference_fnc(node) == "A"


def test_create_topology_cytoscape_simple():
    """Verify simple graph conversion to Cytoscape JSON."""
    g = Graph()
    a = Graphable("A")
    b = Graphable("B")
    g.add_edge(a, b, weight=10)

    output = create_topology_cytoscape(g)
    data = json.loads(output)

    # Expected: 2 nodes, 1 edge
    assert len(data) == 3

    nodes = [
        item for item in data if "source" not in item["data"] and "id" in item["data"]
    ]
    edges = [item for item in data if "source" in item["data"]]

    assert len(nodes) == 2
    assert len(edges) == 1

    # Nodes might be in any order depending on topo sort
    node_ids = {n["data"]["id"] for n in nodes}
    assert node_ids == {"A", "B"}

    assert edges[0]["data"]["source"] == "A"
    assert edges[0]["data"]["target"] == "B"
    assert edges[0]["data"]["weight"] == 10


def test_create_topology_cytoscape_with_tags():
    """Verify node tags are included in Cytoscape JSON."""
    g = Graph()
    a = Graphable("A")
    a.add_tag("v1")
    g.add_node(a)

    output = create_topology_cytoscape(g)
    data = json.loads(output)

    assert data[0]["data"]["tags"] == ["v1"]


def test_export_topology_cytoscape(tmp_path):
    """Verify file writing functionality for Cytoscape."""
    g = Graph()
    g.add_node(Graphable("A"))

    output_file = tmp_path / "graph.cy.json"
    export_topology_cytoscape(g, output_file)

    assert output_file.exists()
    with open(output_file, "r") as f:
        data = json.load(f)
        assert data[0]["data"]["id"] == "A"


def test_create_topology_cytoscape_custom_data():
    """Verify custom data mapping functions in Cytoscape JSON."""
    g = Graph()
    a = Graphable("A")
    b = Graphable("B")
    g.add_edge(a, b)

    config = CytoscapeStylingConfig(
        node_data_fnc=lambda n: {"extra_node": True},
        edge_data_fnc=lambda u, v: {"extra_edge": True},
    )

    output = create_topology_cytoscape(g, config)
    data = json.loads(output)

    nodes = [item for item in data if "source" not in item["data"]]
    edges = [item for item in data if "source" in item["data"]]

    assert all(n["data"]["extra_node"] is True for n in nodes)
    assert all(e["data"]["extra_edge"] is True for e in edges)
