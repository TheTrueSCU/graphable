from __future__ import annotations

from graphlib import TopologicalSorter
from typing import Any, Callable

from .graphable import Graphable


class Graph[T: Graphable[Any, Any]]:
    def __init__(self, initial: set[T] | None = None):
        self._nodes: set[T] = initial if initial else set[T]()
        self._topological_order: list[T] | None = None

    def add_node(self, node: T) -> None:
        self._nodes.add(node)

        if self._topological_order is not None:
            self._topological_order = None

    def filtered_topological_order(self, fn: Callable[[T], bool]) -> list[T]:
        return [node for node in self.topological_order() if fn(node)]

    @property
    def sinks(self) -> list[T]:
        return [node for node in self._nodes if 0 == len(node.dependents)]

    @property
    def sources(self) -> list[T]:
        return [node for node in self._nodes if 0 == len(node.depends_on)]

    def subgraph(self, contains: set[T]) -> Graph[T]:
        def go_down(node: T, nodes: set[T]) -> None:
            for down_node in node.dependents:
                if down_node in nodes:
                    continue

                nodes.add(down_node)
                go_down(down_node, nodes)

        def go_up(node: T, nodes: set[T]) -> None:
            for up_node in node.depends_on:
                if up_node in nodes:
                    continue

                nodes.add(up_node)
                go_up(up_node, nodes)

        nodes: set[T] = set(contains)
        for node in contains:
            go_up(node, nodes)
            go_down(node, nodes)

        return Graph(nodes)

    def topological_order(self) -> list[T]:
        if self._topological_order is None:
            sorter = TopologicalSorter({node: node.depends_on for node in self._nodes})
            self._topological_order = list(sorter.static_order())

        return self._topological_order
