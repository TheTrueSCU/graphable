from __future__ import annotations

import copy
from logging import getLogger
from typing import Any

from .acyclic_graph import AcyclicGraph
from .enums import Direction
from .graph_base import GraphBase
from .graphable import Graphable

logger = getLogger(__name__)


class CyclicGraph[T: Graphable[Any]](GraphBase[T]):
    """
    Represents a graph that may contain cycles.
    """

    def to_acyclic(self) -> AcyclicGraph[T]:
        """
        Create an equivalent AcyclicGraph by breaking cycles.
        Uses suggest_cycle_breaks to identify edges to remove.

        Returns:
            AcyclicGraph[T]: A new AcyclicGraph instance.
        """
        logger.info("Converting CyclicGraph to AcyclicGraph.")
        breaks = self.suggest_cycle_breaks()
        if breaks:
            logger.info(f"Breaking {len(breaks)} edges to achieve acyclicity.")

        # Clone nodes and edges, but skip the breaks
        node_map: dict[T, T] = {}
        for node in self._nodes:
            new_node = copy.copy(node)
            # Reset internal edge tracking
            new_node._dependents = {}
            new_node._depends_on = {}
            new_node._tags = set(node.tags)
            node_map[node] = new_node

        new_graph = AcyclicGraph(set(node_map.values()))
        for u in self._nodes:
            for v, attrs in self.neighbors(u, Direction.DOWN):
                if (u, v) not in breaks:
                    new_graph.add_edge(node_map[u], node_map[v], **attrs)

        return new_graph
