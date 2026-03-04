from enum import Enum, auto


class Direction(Enum):
    """Traversal direction for graph operations."""

    UP = auto()  # Towards dependencies (depends_on)
    DOWN = auto()  # Towards dependents (dependents)


class Engine(str, Enum):
    """Supported visualization engines."""

    MERMAID = "mermaid"
    GRAPHVIZ = "graphviz"
    D2 = "d2"
    PLANTUML = "plantuml"
