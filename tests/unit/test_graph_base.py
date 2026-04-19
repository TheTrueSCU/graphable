from json import loads
from unittest.mock import MagicMock, patch

from pytest import fixture, raises

from graphable.enums import Direction
from graphable.graph_base import GraphBase, GraphConsistencyError
from graphable.graphable import Graphable


class TestGraphBase:
    @fixture
    def nodes(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        return a, b, c

    def test_initialization(self):
        g = GraphBase()
        assert len(g.sources) == 0

    def test_add_node(self):
        g = GraphBase()
        node = Graphable("A")
        assert g.add_node(node) is True
        assert g.add_node(node) is False  # Already added
        assert node in g._nodes

    def test_add_edge(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_edge(a, b)

        assert a in g._nodes
        assert b in g._nodes
        assert b in a.dependents
        assert a in b.depends_on

    def test_sinks_and_sources(self, nodes):
        a, b, c = nodes
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, c)

        assert [a] == g.sources
        assert [c] == g.sinks

    def test_subgraph_filtered(self, nodes):
        a, b, c = nodes
        a.add_tag("keep")
        c.add_tag("keep")

        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, c)

        sub = g.subgraph_filtered(lambda n: n.is_tagged("keep"))
        nodes_in_sub = list(sub)
        assert a in nodes_in_sub
        assert c in nodes_in_sub
        assert b in nodes_in_sub

    def test_subgraph_tagged(self, nodes):
        a, b, c = nodes
        a.add_tag("t")
        g = GraphBase()
        g.add_edge(a, b)

        sub = g.subgraph_tagged("t")
        assert b in sub

    def test_checksum_caching(self, nodes):
        a, _, _ = nodes
        g = GraphBase({a})

        # Initial call calculates and caches
        c1 = g.checksum()
        assert g._checksum is not None

        # Subsequent call returns cached value
        c2 = g.checksum()
        assert c1 == c2
        assert g._checksum == c1

        # Adding a tag to a node should invalidate the graph's checksum cache
        a.add_tag("new-tag")
        assert g._checksum is None

        # Recalculate
        c3 = g.checksum()
        assert c3 != c1
        assert g._checksum == c3

    def test_node_tag_invalidates_all_caches(self, nodes):
        a, _, _ = nodes
        g = GraphBase({a})

        g.checksum()
        assert g._checksum is not None

        # Modify node
        a.add_tag("important")
        assert g._checksum is None

    def test_node_edge_removal_invalidates_graph_cache(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_edge(a, b)

        g.checksum()
        assert g._checksum is not None

        # Remove edge via node method directly
        a._remove_dependent(b)
        b._remove_depends_on(a)

        assert g._checksum is None

    def test_multiple_graphs_observing_same_node(self, nodes):
        a, _, _ = nodes
        g1 = GraphBase({a})
        g2 = GraphBase({a})

        g1.checksum()
        g2.checksum()

        assert g1._checksum is not None
        assert g2._checksum is not None

        a.add_tag("shared")

        assert g1._checksum is None
        assert g2._checksum is None

    def test_external_node_change_does_not_affect_checksum(self, nodes):
        a, b, _ = nodes
        a.add_dependent(b)

        g = GraphBase({a})
        c1 = g.checksum()

        # Modifying B (outside G) should NOT change G's checksum
        b.add_tag("external-change")
        c2 = g.checksum()

        assert c1 == c2

    def test_internal_node_change_invalidates_cache(self, nodes):
        a, b, _ = nodes
        g = GraphBase({a, b})
        a.add_dependent(b)

        c1 = g.checksum()
        assert g._checksum is not None

        # Modifying internal node B should invalidate G's cache
        b.add_tag("internal-change")
        assert g._checksum is None
        assert g.checksum() != c1

    def test_discover_pulls_in_external_nodes(self, nodes):
        a, b, c = nodes
        a.add_dependent(b)
        b.add_dependent(c)

        # Graph only starts with A
        g = GraphBase({a})
        assert len(g) == 1
        assert b not in g

        # Discover should pull in B and C
        g.discover()
        assert len(g) == 3
        assert b in g
        assert c in g

        # Now G is an observer for B and C
        g.checksum()
        assert g._checksum is not None
        c.add_tag("new-info")
        assert g._checksum is None

    def test_consistency_broken_depends_on(self):
        a, b = Graphable("A"), Graphable("B")
        a._add_depends_on(b)
        g = GraphBase()
        with raises(GraphConsistencyError):
            g.add_node(a)

    def test_consistency_broken_dependents(self):
        a, b = Graphable("A"), Graphable("B")
        a._add_dependent(b)
        g = GraphBase()
        with raises(GraphConsistencyError):
            g.add_node(a)

    def test_init_with_inconsistency(self):
        a, b = Graphable("A"), Graphable("B")
        a._add_depends_on(b)
        with raises(GraphConsistencyError):
            GraphBase(initial={a, b})

    def test_container_len(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        assert len(g) == 0
        g.add_node(a)
        assert len(g) == 1
        g.add_node(b)
        assert len(g) == 2

    def test_container_iter(self, nodes):
        a, b, c = nodes
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, c)
        assert set(g) == {a, b, c}

    def test_container_contains(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_node(a)
        assert a in g
        assert "A" in g
        assert b not in g

    def test_container_getitem(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_node(a)
        assert g["A"] == a
        with raises(KeyError):
            _ = g["B"]

    def test_remove_edge(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_edge(a, b)
        g.remove_edge(a, b)
        assert b not in a.dependents
        assert a not in b.depends_on

    def test_remove_node(self, nodes):
        a, b, c = nodes
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.remove_node(b)
        assert b not in g
        assert b not in a.dependents

    def test_ancestors_descendants(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.add_edge(c, d)
        assert set(g.ancestors(d)) == {a, b, c}
        assert set(g.descendants(a)) == {b, c, d}

    def test_ancestors_diamond(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)
        assert set(g.ancestors(d)) == {a, b, c}
        assert set(g.descendants(a)) == {b, c, d}

    def test_upstream_downstream_of(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.add_edge(c, d)

        up = g.upstream_of(c)
        assert set(up) == {a, b, c}
        assert d not in up

        down = g.downstream_of(b)
        assert set(down) == {b, c, d}
        assert a not in down

    def test_all_paths(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        d = Graphable("D")
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)

        paths = g.all_paths(a, d)
        assert len(paths) == 2
        assert [a, b, d] in paths
        assert [a, c, d] in paths

    def test_all_paths_cyclic(self):
        a, b, c = [Graphable(x) for x in "ABC"]
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, a)  # Cycle A <-> B
        g.add_edge(b, c)

        # Should only find simple paths
        paths = g.all_paths(a, c)
        assert len(paths) == 1
        assert paths[0] == [a, b, c]

    def test_suggest_cycle_breaks(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")

        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(c)
        c._add_depends_on(b)
        c._add_dependent(a)
        a._add_depends_on(c)

        g = GraphBase()
        g._nodes = {a, b, c}

        breaks = g.suggest_cycle_breaks()
        assert len(breaks) > 0
        u, v = breaks[0]
        assert (u == a and v == b) or (u == b and v == c) or (u == c and v == a)

    def test_subgraph_between(self):
        a, b, c, d, e = [Graphable(x) for x in "ABCDE"]
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(b, d)
        g.add_edge(a, c)
        g.add_edge(c, d)
        g.add_edge(d, e)

        sub = g.subgraph_between(a, d)
        assert set(sub) == {a, b, c, d}
        assert e not in sub

    def test_diff_graph(self):
        a1, b1 = Graphable("A"), Graphable("B")
        g1 = GraphBase()
        g1.add_edge(a1, b1)

        a2, c2 = Graphable("A"), Graphable("C")
        g2 = GraphBase()
        g2.add_edge(a2, c2)

        dg = g1.diff_graph(g2)
        nodes = {n.reference: n for n in dg}
        assert "A" in nodes
        assert "B" in nodes
        assert "C" in nodes

        assert nodes["B"].is_tagged("diff:removed")
        assert nodes["C"].is_tagged("diff:added")

        assert nodes["A"].edge_attributes(nodes["B"])["color"] == "red"
        assert nodes["A"].edge_attributes(nodes["C"])["color"] == "green"

    def test_graph_render_convenience(self):
        a, b = Graphable("A"), Graphable("B")
        g = GraphBase()
        g.add_edge(a, b)
        from graphable.views.mermaid import create_topology_mermaid_mmd

        out = g.render(create_topology_mermaid_mmd)
        assert "A --> B" in out

    def test_graph_export_convenience(self, tmp_path):
        a, b = Graphable("A"), Graphable("B")
        g = GraphBase()
        g.add_edge(a, b)
        from graphable.views.mermaid import export_topology_mermaid_mmd

        output_file = tmp_path / "graph.mmd"
        g.export(export_topology_mermaid_mmd, output=output_file)
        assert output_file.exists()

    def test_checksum_deterministic(self):
        a1, b1 = Graphable("A"), Graphable("B")
        g1 = GraphBase()
        g1.add_edge(a1, b1)
        b2, a2 = Graphable("B"), Graphable("A")
        g2 = GraphBase()
        g2.add_edge(a2, b2)
        assert g1.checksum() == g2.checksum()

    def test_validate_checksum(self):
        a = Graphable("A")
        g = GraphBase()
        g.add_node(a)
        digest = g.checksum()
        assert g.validate_checksum(digest) is True

    def test_read_write_auto_detect(self, tmp_path):
        a, b = Graphable("A"), Graphable("B")
        g: GraphBase[Graphable[str]] = GraphBase()
        g.add_edge(a, b)
        json_file = tmp_path / "graph.json"
        g.write(json_file)
        g_read = GraphBase.read(json_file)
        assert g == g_read

    def test_standalone_checksum_io(self, tmp_path):
        a = Graphable("A")
        g: GraphBase[Graphable[str]] = GraphBase()
        g.add_node(a)
        sum_file = tmp_path / "graph.blake2b"
        g.write_checksum(sum_file)
        digest = GraphBase.read_checksum(sum_file)
        assert digest == g.checksum()

    def test_embedded_checksum_io(self, tmp_path):
        a, b = Graphable("A"), Graphable("B")
        g: GraphBase[Graphable[str]] = GraphBase()
        g.add_edge(a, b)
        yaml_file = tmp_path / "embedded.yaml"
        g.write(yaml_file, embed_checksum=True)
        assert "blake2b:" in yaml_file.read_text()
        g_read = GraphBase.read(yaml_file)
        assert g == g_read

    def test_embedded_checksum_json_wrapping(self, tmp_path):
        a = Graphable("A")
        g: GraphBase[Graphable[str]] = GraphBase()
        g.add_node(a)

        json_file = tmp_path / "embedded.json"
        g.write(json_file, embed_checksum=True)

        data = loads(json_file.read_text())
        assert "checksum" in data
        assert "graph" in data
        assert data["graph"]["nodes"][0]["id"] == "A"

        g_read = GraphBase.read(json_file)
        assert g == g_read

    def test_clone(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_edge(a, b, weight=5)
        a.add_tag("t1")

        c1 = g.clone(include_edges=False)
        assert len(c1) == 2
        assert len(list(c1.neighbors(c1["A"]))) == 0
        assert "t1" in c1["A"].tags
        assert c1["A"] is not a

        c2 = g.clone(include_edges=True)
        assert len(c2) == 2
        assert len(list(c2.neighbors(c2["A"]))) == 1
        assert c2["A"].edge_attributes(c2["B"])["weight"] == 5

    def test_checksum_includes_metadata(self, nodes):
        a, b, _ = nodes
        g = GraphBase({a, b})
        g.add_edge(a, b, weight=10)

        c1 = g.checksum()

        a.duration = 1.0
        c2 = g.checksum()
        assert c1 != c2

        b.status = "completed"
        c3 = g.checksum()
        assert c2 != c3

        a.set_edge_attribute(b, "weight", 20)
        c4 = g.checksum()
        assert c3 != c4

    def test_export_fallback(self, tmp_path):
        g = GraphBase([Graphable("A")])

        def mock_exporter(graph, path):
            with open(path, "w") as f:
                f.write("mock output")

        output = tmp_path / "mock.txt"
        g.export(mock_exporter, output, embed_checksum=True)
        assert output.read_text() == "mock output"

    def test_bfs_dfs(self):
        a, b, c, d = [Graphable(x) for x in "ABCD"]
        g = GraphBase()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)

        bfs_nodes = list(g.bfs(a))
        assert bfs_nodes[0] == a
        assert set(bfs_nodes[1:3]) == {b, c}
        assert bfs_nodes[3] == d

        dfs_nodes = list(g.dfs(a))
        assert len(dfs_nodes) == 4
        assert dfs_nodes[0] == a

    def test_write_unsupported_extension(self):
        g = GraphBase()
        with raises(ValueError, match="Unsupported extension: .invalid"):
            g.write("test.invalid")

    @patch("graphable.views.utils.get_image_exporter")
    def test_write_image_logic(self, mock_get_exporter):
        mock_exporter = MagicMock()
        mock_get_exporter.return_value = mock_exporter
        g = GraphBase()
        g.write("test.png", engine="mermaid")
        mock_get_exporter.assert_called_with("mermaid")
        mock_exporter.assert_called_once()

    def test_diff_graph_complex(self):
        g1 = GraphBase()
        a1 = Graphable("A")
        b1 = Graphable("B")
        g1.add_edge(a1, b1, weight=1)

        g2 = GraphBase()
        a2 = Graphable("A")
        b2 = Graphable("B")
        c2 = Graphable("C")
        g2.add_edge(a2, b2, weight=2)
        g2.add_edge(b2, c2)

        dg = g1.diff_graph(g2)
        assert len(dg) == 3

    def test_neighbors(self, nodes):
        a, b, _ = nodes
        g = GraphBase()
        g.add_edge(a, b, weight=1)

        neighbors = list(g.neighbors(a, Direction.DOWN))
        assert len(neighbors) == 1
        assert neighbors[0][0] == b
        assert neighbors[0][1]["weight"] == 1

        rev_neighbors = list(g.neighbors(b, Direction.UP))
        assert len(rev_neighbors) == 1
        assert rev_neighbors[0][0] == a
        assert rev_neighbors[0][1]["weight"] == 1
