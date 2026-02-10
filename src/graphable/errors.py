from typing import Any


class GraphCycleError(Exception):
    """
    Exception raised when a cycle is detected in the graph.
    """

    def __init__(self, message: str, cycle: list[Any] | None = None):
        super().__init__(message)
        self.cycle = cycle


class GraphConsistencyError(Exception):
    """
    Exception raised when the bi-directional relationships in the graph are inconsistent.
    """

    pass
