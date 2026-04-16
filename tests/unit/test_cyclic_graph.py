from pytest import fixture

from graphable.acyclic_graph import AcyclicGraph
from graphable.cyclic_graph import CyclicGraph
from graphable.graphable import Graphable


class TestCyclicGraph:
    @fixture
    def nodes(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")
        return a, b, c

    def test_initialization_with_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(a)
        a._add_depends_on(b)

        # Should NOT raise GraphCycleError
        g = CyclicGraph(initial={a, b})
        assert len(g) == 2

    def test_add_edge_cycle(self):
        a = Graphable("A")
        b = Graphable("B")
        g = CyclicGraph()
        g.add_edge(a, b)
        # Should NOT raise GraphCycleError
        g.add_edge(b, a)
        assert len(g) == 2
        assert b in a.dependents
        assert a in b.dependents

    def test_to_acyclic(self):
        a = Graphable("A")
        b = Graphable("B")
        c = Graphable("C")

        # Create cycle A -> B -> C -> A
        a._add_dependent(b)
        b._add_depends_on(a)
        b._add_dependent(c)
        c._add_depends_on(b)
        c._add_dependent(a)
        a._add_depends_on(c)

        g = CyclicGraph(initial={a, b, c})
        assert len(g) == 3

        dag = g.to_acyclic()
        assert isinstance(dag, AcyclicGraph)
        assert len(dag) == 3

        # Check that it's actually acyclic
        dag.check_cycles()

        # One edge should have been removed
        total_edges = 0
        for node in dag:
            total_edges += len(list(dag.neighbors(node)))
        assert total_edges == 2
