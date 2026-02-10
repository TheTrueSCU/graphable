import networkx as nx
from pytest import raises

from graphable.graph import Graph
from graphable.graphable import Graphable


class TestNetworkX:
    def test_to_networkx(self):
        a = Graphable("A")
        b = Graphable("B")
        a.add_tag("source")
        g = Graph()
        g.add_edge(a, b)

        dg = g.to_networkx()

        assert isinstance(dg, nx.DiGraph)
        assert "A" in dg.nodes
        assert "B" in dg.nodes
        assert dg.has_edge("A", "B")

        # Check metadata
        assert dg.nodes["A"]["reference"] == "A"
        assert dg.nodes["A"]["tags"] == ["source"]

    def test_to_networkx_missing_library(self, monkeypatch):
        # Temporarily hide networkx to test ImportError
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "networkx":
                raise ImportError("mocked error")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        g = Graph()
        with raises(ImportError) as excinfo:
            g.to_networkx()
        assert "networkx is required" in str(excinfo.value)
