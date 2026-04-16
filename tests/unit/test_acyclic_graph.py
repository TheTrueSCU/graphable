from pytest import fixture, raises

from graphable.acyclic_graph import AcyclicGraph
from graphable.errors import GraphCycleError
from graphable.graphable import Graphable


class TestAcyclicGraph:
    @fixture
    def nodes(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        return a, b, c

    def test_initialization(self):
        g = AcyclicGraph()
        assert len(g.sources) == 0

    def test_topological_order(self, nodes):
        a, b, c = nodes
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        topo = g.topological_order()
        assert topo.index(a) < topo.index(b)
        assert topo.index(b) < topo.index(c)

    def test_topological_order_filtered(self, nodes):
        a, b, c = nodes
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        filtered = g.topological_order_filtered(lambda n: n.reference == "B")
        assert len(filtered) == 1
        assert filtered[0] == b

    def test_topological_order_tagged(self, nodes):
        a, b, c = nodes
        b.add_tag("target")
        g = AcyclicGraph()
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

        g = AcyclicGraph([b], discover=True)
        topo = g.topological_order()
        assert len(topo) == 3
        assert a in topo
        assert c in topo

    def test_topological_order_caching(self, nodes):
        a, b, _ = nodes
        g = AcyclicGraph({a, b})

        topo1 = g.topological_order()
        assert g._topological_order is not None
        topo2 = g.topological_order()
        assert topo1 is topo2

        c = Graphable("C")
        g.add_node(c)
        assert g._topological_order is None

        topo3 = g.topological_order()
        assert g._topological_order is not None
        assert c in topo3

    def test_parallelized_topological_order_caching(self, nodes):
        a, b, _ = nodes
        a.add_dependent(b)
        g = AcyclicGraph({a, b})

        order1 = g.parallelized_topological_order()
        assert g._parallel_topological_order is not None
        assert order1 is g._parallel_topological_order

        order2 = g.parallelized_topological_order()
        assert order2 is order1

        c = Graphable("C")
        g.add_node(c)
        g.add_edge(b, c)
        assert g._parallel_topological_order is None

        order3 = g.parallelized_topological_order()
        assert g._parallel_topological_order is not None
        assert len(order3) == 3

    def test_subgraph_filtering_in_topological_order(self, nodes):
        a, b, _ = nodes
        a.add_dependent(b)
        g = AcyclicGraph({a})
        order = g.topological_order()
        assert order == [a]
        assert b not in order

    def test_add_edge_self_loop(self):
        a = Graphable("A")
        g = AcyclicGraph()
        with raises(GraphCycleError) as excinfo:
            g.add_edge(a, a)
        assert "Self-loop" in str(excinfo.value)

    def test_add_edge_simple_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        g = AcyclicGraph()
        g.add_edge(a, b)
        with raises(GraphCycleError):
            g.add_edge(b, a)

    def test_add_edge_complex_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        with raises(GraphCycleError):
            g.add_edge(c, a)

    def test_add_edge_cycle_with_shared_path(self):
        a, b, c, d, target = [Graphable(x) for x in ["A", "B", "C", "D", "Target"]]
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)
        g.add_edge(d, target)

        with raises(GraphCycleError):
            g.add_edge(target, a)

    def test_add_node_with_existing_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)

        g = AcyclicGraph()
        with raises(GraphCycleError):
            g.add_node(a)

    def test_init_with_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)
        with raises(GraphCycleError):
            AcyclicGraph(initial={a, b})

    def test_check_cycles_manual(self):
        a, b = Graphable("A"), Graphable("B")
        g = AcyclicGraph()
        g._nodes.add(a)
        g._nodes.add(b)
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)
        with raises(GraphCycleError):
            g.check_cycles()

    def test_cpm_and_longest_path(self):
        a, b, c, d = [Graphable(x) for x in "ABCD"]
        a.duration, b.duration, c.duration, d.duration = 2, 3, 1, 4
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)

        analysis = g.cpm_analysis()
        assert analysis[d]["EF"] == 9
        assert analysis[b]["slack"] == 0
        assert analysis[c]["slack"] == 2

        cp = g.critical_path()
        assert set(cp) == {a, b, d}

        lp = g.longest_path()
        assert lp == [a, b, d]

    def test_transitive_closure(self):
        a, b, c = [Graphable(x) for x in "ABC"]
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        closure = g.transitive_closure()
        assert len(closure) == 3
        nodes = {n.reference: n for n in closure}
        assert nodes["C"] in nodes["A"].dependents

    def test_transitive_reduction_simple(self):
        a, b, c = [Graphable(x) for x in "ABC"]
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(b, c)
        g.add_edge(a, c)
        reduced = g.transitive_reduction()
        assert len(list(reduced.neighbors(reduced["A"]))) == 1

    def test_parallelized_topological_order(self):
        a, b, c, d = [Graphable(x) for x in "ABCD"]
        g = AcyclicGraph()
        g.add_edge(a, b)
        g.add_edge(a, c)
        g.add_edge(b, d)
        g.add_edge(c, d)
        layers = g.parallelized_topological_order()
        assert len(layers) == 3
        assert layers[1] == {b, c}

    def test_parallelized_topological_order_filtered(self):
        g = AcyclicGraph()
        a, b = Graphable("A"), Graphable("B")
        g.add_edge(a, b)
        order = g.parallelized_topological_order_filtered(lambda n: n.reference == "A")
        assert len(order) == 1
        assert list(order[0])[0].reference == "A"

    def test_parallelized_topological_order_tagged(self):
        g = AcyclicGraph()
        a, b = Graphable("A"), Graphable("B")
        a.add_tag("v1")
        g.add_node(a)
        g.add_node(b)
        order = g.parallelized_topological_order_tagged("v1")
        assert len(order) == 1
        assert list(order[0])[0].reference == "A"
