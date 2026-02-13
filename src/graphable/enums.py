from enum import Enum, auto


class Direction(Enum):
    """Traversal direction for graph operations."""

    UP = auto()  # Towards dependencies (depends_on)
    DOWN = auto()  # Towards dependents (dependents)
