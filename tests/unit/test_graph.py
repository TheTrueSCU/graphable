from pytest import fixture, raises

from graphable.graph import Graph, GraphConsistencyError, GraphCycleError, graph
from graphable.graphable import Graphable


class TestGraph:
    @fixture
    def nodes(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        return a, b, c

    def test_initialization(self):
        g = Graph()
        assert len(g.sources) == 0

    def test_add_node(self):
        g = Graph()
        node = Graphable("A")
        assert g.add_node(node) is True
        assert g.add_node(node) is False  # Already added
        assert node in g._nodes

    def test_add_edge(self, nodes):
        a, b, _ = nodes
        g = Graph()
        g.add_edge(a, b)

        assert a in g._nodes
        assert b in g._nodes
        assert b in a.dependents
        assert a in b.depends_on

    def test_sinks_and_sources(self, nodes):
        a, b, c = nodes
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        assert [a] == g.sources
        assert [c] == g.sinks

    def test_topological_order(self, nodes):
        a, b, c = nodes
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        topo = g.topological_order()
        assert topo.index(a) < topo.index(b)
        assert topo.index(b) < topo.index(c)

    def test_subgraph_filtered(self, nodes):
        a, b, c = nodes
        a.add_tag("keep")
        c.add_tag("keep")

        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        sub = g.subgraph_filtered(lambda n: n.is_tagged("keep"))
        nodes_in_sub = sub.topological_order()
        assert a in nodes_in_sub
        assert c in nodes_in_sub
        assert b in nodes_in_sub

    def test_subgraph_tagged(self, nodes):
        a, b, c = nodes
        a.add_tag("t")
        g = Graph()
        g.add_edge(a, b)

        sub = g.subgraph_tagged("t")
        assert b in sub.topological_order()

    def test_topological_order_filtered(self, nodes):
        a, b, c = nodes
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        filtered = g.topological_order_filtered(lambda n: n.reference == "B")
        assert len(filtered) == 1
        assert filtered[0] == b

    def test_topological_order_tagged(self, nodes):
        a, b, c = nodes
        b.add_tag("target")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        tagged = g.topological_order_tagged("target")
        assert len(tagged) == 1
        assert tagged[0] == b

    def test_graph_factory(self, nodes):
        a, b, c = nodes
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(c)
        c._add_depends_on(b)

        g = graph([b])
        topo = g.topological_order()
        assert len(topo) == 3
        assert a in topo
        assert c in topo

    def test_topological_order_caching(self, nodes):
        a, b, _ = nodes
        g = Graph({a, b})

        # Initial call calculates and caches
        topo1 = g.topological_order()
        assert g._topological_order is not None

        # Subsequent call returns cached value
        topo2 = g.topological_order()
        assert topo1 is topo2

        # Adding a node invalidates cache
        c = Graphable("C")
        g.add_node(c)
        assert g._topological_order is None

        # Recalculate
        topo3 = g.topological_order()
        assert g._topological_order is not None
        assert c in topo3

    def test_checksum_caching(self, nodes):
        a, _, _ = nodes
        g = Graph({a})

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

    def test_parallelized_topological_order_caching(self, nodes):
        a, b, _ = nodes
        a.add_dependent(b)
        g = Graph({a, b})

        # Initial call calculates and caches
        order1 = g.parallelized_topological_order()
        assert g._parallel_topological_order is not None
        assert order1 is g._parallel_topological_order

        # Subsequent call uses cached value
        order2 = g.parallelized_topological_order()
        assert order2 is order1

        # Adding an edge should invalidate cache
        c = Graphable("C")
        g.add_node(c)
        g.add_edge(b, c)
        assert g._parallel_topological_order is None

        # Recalculate
        order3 = g.parallelized_topological_order()
        assert g._parallel_topological_order is not None
        assert len(order3) == 3  # A, B, C in separate layers

    def test_node_tag_invalidates_all_caches(self, nodes):
        a, _, _ = nodes
        g = Graph({a})

        g.topological_order()
        g.parallelized_topological_order()
        g.checksum()

        assert g._topological_order is not None
        assert g._parallel_topological_order is not None
        assert g._checksum is not None

        # Modify node
        a.add_tag("important")

        assert g._topological_order is None
        assert g._parallel_topological_order is None
        assert g._checksum is None

    def test_node_dependency_change_invalidates_all_caches(self, nodes):
        a, b, _ = nodes
        g = Graph({a, b})

        g.topological_order()
        g.parallelized_topological_order()
        g.checksum()

        assert g._topological_order is not None
        assert g._parallel_topological_order is not None
        assert g._checksum is not None

        # Modify node dependency externally (not via graph.add_edge)
        a.add_dependent(b)

        assert g._topological_order is None
        assert g._parallel_topological_order is None
        assert g._checksum is None

    def test_node_edge_removal_invalidates_graph_cache(self, nodes):
        a, b, _ = nodes
        g = Graph()
        g.add_edge(a, b)

        g.checksum()
        assert g._checksum is not None

        # Remove edge via node method directly
        a._remove_dependent(b)
        b._remove_depends_on(a)

        assert g._checksum is None

    def test_multiple_graphs_observing_same_node(self, nodes):
        a, _, _ = nodes
        g1 = Graph({a})
        g2 = Graph({a})

        g1.checksum()
        g2.checksum()

        assert g1._checksum is not None
        assert g2._checksum is not None

        a.add_tag("shared")

        assert g1._checksum is None
        assert g2._checksum is None

    def test_subgraph_filtering_in_topological_order(self, nodes):
        a, b, _ = nodes
        a.add_dependent(b)

        # Graph only contains A
        g = Graph({a})

        # B should not be in the results even though it's a dependent
        order = g.topological_order()
        assert order == [a]
        assert b not in order

        parallel = g.parallelized_topological_order()
        assert parallel == [{a}]

    def test_external_node_change_does_not_affect_checksum(self, nodes):
        a, b, _ = nodes
        a.add_dependent(b)

        g = Graph({a})
        c1 = g.checksum()

        # Modifying B (outside G) should NOT change G's checksum
        # because we only include internal edges now.
        b.add_tag("external-change")
        c2 = g.checksum()

        assert c1 == c2

    def test_internal_node_change_invalidates_cache(self, nodes):
        a, b, _ = nodes
        g = Graph({a, b})
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
        g = Graph({a})
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

    def test_add_edge_self_loop(self):
        a = Graphable("A")
        g = Graph()
        with raises(GraphCycleError) as excinfo:
            g.add_edge(a, a)
        assert "Self-loop" in str(excinfo.value)
        assert excinfo.value.cycle == [a, a]

    def test_add_edge_simple_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        with raises(GraphCycleError) as excinfo:
            g.add_edge(b, a)
        assert "create a cycle" in str(excinfo.value)
        assert excinfo.value.cycle is not None
        assert a in excinfo.value.cycle
        assert b in excinfo.value.cycle

    def test_add_edge_complex_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        with raises(GraphCycleError) as excinfo:
            g.add_edge(c, a)
        assert "create a cycle" in str(excinfo.value)
        assert excinfo.value.cycle is not None
        assert a in excinfo.value.cycle
        assert b in excinfo.value.cycle
        assert c in excinfo.value.cycle

    def test_add_edge_cycle_with_shared_path(self):
        a, b, c, d, target = (
            Graphable("A"),
            Graphable("B"),
            Graphable("C"),
            Graphable("D"),
            Graphable("Target"),
        )
        graph_obj = Graph()
        graph_obj.add_edge(a, b)
        graph_obj.add_edge(a, c)
        graph_obj.add_edge(b, d)
        graph_obj.add_edge(c, d)
        graph_obj.add_edge(d, target)

        assert a.find_path(target) is not None
        with raises(GraphCycleError):
            graph_obj.add_edge(target, a)

    def test_add_node_with_existing_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)

        g = Graph()
        with raises(GraphCycleError) as excinfo:
            g.add_node(a)
        assert "existing cycle" in str(excinfo.value)

    def test_init_with_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)
        with raises(GraphCycleError):
            Graph(initial={a, b})

    def test_check_cycles_manual(self):
        a, b = Graphable("A"), Graphable("B")
        g = Graph()
        g.add_node(a)
        g.add_node(b)
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)
        with raises(GraphCycleError):
            g.check_cycles()

    def test_consistency_broken_depends_on(self):
        a, b = Graphable("A"), Graphable("B")
        a._add_depends_on(b)
        g = Graph()
        with raises(GraphConsistencyError):
            g.add_node(a)

    def test_consistency_broken_dependents(self):
        a, b = Graphable("A"), Graphable("B")
        a._add_dependent(b)
        g = Graph()
        with raises(GraphConsistencyError):
            g.add_node(a)

    def test_init_with_inconsistency(self):
        a, b = Graphable("A"), Graphable("B")
        a._add_depends_on(b)
        with raises(GraphConsistencyError):
            Graph(initial={a, b})

    def test_container_len(self, nodes):
        a, b, _ = nodes
        g = Graph()
        assert len(g) == 0
        g.add_node(a)
        assert len(g) == 1
        g.add_node(b)
        assert len(g) == 2

    def test_container_iter(self, nodes):
        a, b, c = nodes
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        assert list(g) == [a, b, c]

    def test_container_contains(self, nodes):
        a, b, _ = nodes
        g = Graph()
        g.add_node(a)
        assert a in g
        assert "A" in g
        assert b not in g

    def test_container_getitem(self, nodes):
        a, b, _ = nodes
        g = Graph()
        g.add_node(a)
        assert g["A"] == a
        with raises(KeyError):
            _ = g["B"]

    def test_remove_edge(self, nodes):
        a, b, _ = nodes
        g = Graph()
        g.add_edge(a, b)
        g.remove_edge(a, b)
        assert b not in a.dependents
        assert a not in b.depends_on

    def test_remove_node(self, nodes):
        a, b, c = nodes
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.remove_node(b)
        assert b not in g
        assert b not in a.dependents

    def test_ancestors_descendants(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.add_edge(c, d)
        assert set(g.ancestors(d)) == {a, b, c}
        assert set(g.descendants(a)) == {b, c, d}

    def test_ancestors_diamond(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)
        assert set(g.ancestors(d)) == {a, b, c}
        assert set(g.descendants(a)) == {b, c, d}

    def test_transitive_reduction_simple(self):
        a, b, c = Graphable("A"), Graphable("B"), Graphable("C")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.add_edge(a, c)
        reduced = g.transitive_reduction()
        assert len(reduced["A"].dependents) == 1

    def test_transitive_reduction_diamond(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, d)
        g.add_edge(a, c)
        g.add_edge(c, d)
        g.add_edge(a, d)
        reduced = g.transitive_reduction()
        assert len(reduced["A"].dependents) == 2
        assert reduced["D"] not in reduced["A"].dependents

    def test_transitive_reduction_preserves_tags(self):
        a, b = Graphable("A"), Graphable("B")
        a.add_tag("important")
        g = Graph()
        g.add_edge(a, b)
        reduced = g.transitive_reduction()
        assert "important" in reduced["A"].tags
        reduced["A"].add_tag("reduced-only")
        assert "reduced-only" not in g["A"].tags

    def test_graph_render_convenience(self):
        a, b = Graphable("A"), Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        from graphable.views.mermaid import create_topology_mermaid_mmd

        out = g.render(create_topology_mermaid_mmd)
        assert "A --> B" in out

    def test_graph_export_convenience(self, tmp_path):
        a, b = Graphable("A"), Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        from graphable.views.mermaid import export_topology_mermaid_mmd

        output_file = tmp_path / "graph.mmd"
        g.export(export_topology_mermaid_mmd, output=output_file)
        assert output_file.exists()

    def test_checksum_deterministic(self):
        a1, b1 = Graphable("A"), Graphable("B")
        g1 = Graph()
        g1.add_edge(a1, b1)
        b2, a2 = Graphable("B"), Graphable("A")
        g2 = Graph()
        g2.add_edge(a2, b2)
        assert g1.checksum() == g2.checksum()

    def test_parallelized_topological_order(self):
        a, b, c, d = Graphable("A"), Graphable("B"), Graphable("C"), Graphable("D")
        g = Graph()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)
        layers = g.parallelized_topological_order()
        assert len(layers) == 3
        assert layers[1] == {b, c}

    def test_validate_checksum(self):
        a = Graphable("A")
        g = Graph()
        g.add_node(a)
        digest = g.checksum()
        assert g.validate_checksum(digest) is True

    def test_read_write_auto_detect(self, tmp_path):
        a, b = Graphable("A"), Graphable("B")
        g: Graph[Graphable[str]] = Graph()
        g.add_edge(a, b)
        json_file = tmp_path / "graph.json"
        g.write(json_file)
        g_read = Graph.read(json_file)
        assert g == g_read

    def test_standalone_checksum_io(self, tmp_path):
        a = Graphable("A")
        g: Graph[Graphable[str]] = Graph()
        g.add_node(a)
        sum_file = tmp_path / "graph.blake2b"
        g.write_checksum(sum_file)
        digest = Graph.read_checksum(sum_file)
        assert digest == g.checksum()

    def test_embedded_checksum_io(self, tmp_path):
        a, b = Graphable("A"), Graphable("B")
        g: Graph[Graphable[str]] = Graph()
        g.add_edge(a, b)
        yaml_file = tmp_path / "embedded.yaml"
        g.write(yaml_file, embed_checksum=True)
        assert "blake2b:" in yaml_file.read_text()
        g_read = Graph.read(yaml_file)
        assert g == g_read

    def test_embedded_checksum_json_wrapping(self, tmp_path):
        a = Graphable("A")
        g: Graph[Graphable[str]] = Graph()
        g.add_node(a)

        json_file = tmp_path / "embedded.json"
        g.write(json_file, embed_checksum=True)

        # Verify it is valid JSON
        import json

        data = json.loads(json_file.read_text())
        assert "checksum" in data
        assert "graph" in data
        assert data["graph"]["nodes"][0]["id"] == "A"

        # Verify it can be read back
        g_read = Graph.read(json_file)
        assert g == g_read
