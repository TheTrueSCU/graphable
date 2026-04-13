import pytest
from hypothesis import given
from hypothesis import strategies as st

from graphable.errors import GraphCycleError
from graphable.graph import Graph
from graphable.graphable import Graphable


# Define a simple Graphable implementation for testing
class Node(Graphable[str]):
    def __init__(self, name: str):
        super().__init__(reference=name)
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Node) and self.name == other.name

    def __repr__(self):
        return f"Node({self.name})"


@st.composite
def graph_strategy(draw):
    """
    Strategy to generate a random directed graph, handling cycle generation gracefully.
    """
    nodes = draw(st.lists(st.text(min_size=1), unique=True, min_size=1))
    node_objects = [Node(n) for n in nodes]

    graph = Graph(initial=node_objects)

    # Generate random edges, ignoring cycle errors
    num_edges = draw(st.integers(min_value=0, max_value=len(nodes) * 2))
    for _ in range(num_edges):
        u = draw(st.sampled_from(node_objects))
        v = draw(st.sampled_from(node_objects))
        if u != v:
            try:
                graph.add_edge(u, v)
            except GraphCycleError:
                continue

    return graph


@given(graph_strategy())
def test_graph_consistency_invariant(graph: Graph[Node]):
    """
    Verify that any generated graph can be checked for consistency.
    """
    # A graph should always be able to run consistency checks without crashing,
    # unless it is structurally invalid.
    try:
        graph.check_consistency()
    except Exception as e:
        pytest.fail(f"Consistency check failed on valid generated graph: {e}")


@given(graph_strategy())
def test_clone_preserves_nodes(graph: Graph[Node]):
    """
    Verify that a cloned graph contains the same number of nodes.
    """
    cloned = graph.clone(include_edges=True)
    assert len(cloned._nodes) == len(graph._nodes)
    for node in graph._nodes:
        assert node in cloned._nodes
