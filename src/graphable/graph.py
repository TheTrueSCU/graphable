from __future__ import annotations

from .acyclic_graph import AcyclicGraph
from .cyclic_graph import CyclicGraph
from .graph_base import GraphBase

# Default Graph to AcyclicGraph for backwards compatibility
Graph = AcyclicGraph

__all__ = ["AcyclicGraph", "CyclicGraph", "Graph", "GraphBase"]
