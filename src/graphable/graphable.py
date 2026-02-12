import weakref
from collections import deque
from logging import getLogger
from typing import Any, Self, cast

from .errors import GraphCycleError

logger = getLogger(__name__)


class Graphable[T]:
    """
    A generic class representing a node in a graph that can track dependencies and dependents.

    Type Parameters:
        T: The type of the reference object this node holds.
    """

    def __init__(self, reference: T):
        """
        Initialize a Graphable node.

        Args:
            reference (T): The underlying object this node represents.
        """
        self._dependents: set[Graphable[Any]] = set()
        self._depends_on: set[Graphable[Any]] = set()
        self._reference: T = reference
        self._tags: set[str] = set()
        self._observers: weakref.WeakSet[Any] = weakref.WeakSet()
        logger.debug(f"Created Graphable node for reference: {reference}")

    def _notify_change(self) -> None:
        """Notify all observers that this node has changed."""
        for observer in list(self._observers):
            if hasattr(observer, "_invalidate_cache"):
                observer._invalidate_cache()

    def _register_observer(self, observer: Any) -> None:
        """Register an observer to be notified of changes."""
        self._observers.add(observer)

    def _unregister_observer(self, observer: Any) -> None:
        """Unregister an observer."""
        self._observers.discard(observer)

    def __eq__(self, other: object) -> bool:
        """
        Check if this node is equal to another.
        Nodes are considered equal if they are the same object.
        """
        return self is other

    def __hash__(self) -> int:
        """
        Restore default hash behavior (identity-based).
        """
        return id(self)

    def __lt__(self, other: object) -> bool:
        """
        Check if this node is 'less than' another.
        Defined as: this node is a proper ancestor of the other node.
        """
        if not isinstance(other, Graphable):
            return NotImplemented

        return self.find_path(other) is not None

    def __le__(self, other: object) -> bool:
        """
        Check if this node is 'less than or equal' to another.
        Defined as: this node is an ancestor of or identical to the other node.
        """
        if not isinstance(other, Graphable):
            return NotImplemented

        return self is other or self.find_path(other) is not None

    def __gt__(self, other: object) -> bool:
        """
        Check if this node is 'greater than' another.
        Defined as: this node is a proper descendant of the other node.
        """
        if not isinstance(other, Graphable):
            return NotImplemented

        return other.find_path(self) is not None

    def __ge__(self, other: object) -> bool:
        """
        Check if this node is 'greater than or equal' to another.
        Defined as: this node is a descendant of or identical to the other node.
        """
        if not isinstance(other, Graphable):
            return NotImplemented

        return self is other or other.find_path(self) is not None

    def add_dependencies(
        self, dependencies: set[Self], check_cycles: bool = False
    ) -> None:
        """
        Add multiple dependencies to this node.

        Args:
            dependencies (set[Self]): A set of Graphable nodes to add as dependencies.
            check_cycles (bool): If True, check if adding these dependencies would create a cycle.
        """
        logger.debug(f"Node '{self.reference}': adding dependencies {dependencies}")
        for dependency in dependencies:
            self.add_dependency(dependency, check_cycles=check_cycles)

    def add_dependency(self, dependency: Self, check_cycles: bool = False) -> None:
        """
        Add a single dependency to this node.

        Args:
            dependency (Self): The Graphable node to add as a dependency.
            check_cycles (bool): If True, check if adding this dependency would create a cycle.

        Raises:
            GraphCycleError: If check_cycles is True and a cycle would be created.
        """
        if check_cycles:
            logger.debug(
                f"Checking if adding dependency '{dependency.reference}' to '{self.reference}' creates a cycle"
            )
            if path := self.find_path(dependency):
                cycle = path + [self]
                logger.error(
                    f"Cycle detected: {' -> '.join(str(n.reference) for n in cycle)}"
                )
                raise GraphCycleError(
                    f"Adding dependency '{dependency.reference}' to "
                    f"'{self.reference}' would create a cycle.",
                    cycle=cycle,
                )

        logger.debug(
            f"Node '{self.reference}': adding dependency '{dependency.reference}'"
        )
        self._add_depends_on(dependency)
        dependency._add_dependent(self)

    def add_dependent(self, dependent: Self, check_cycles: bool = False) -> None:
        """
        Add a single dependent to this node.

        Args:
            dependent (Self): The Graphable node to add as a dependent.
            check_cycles (bool): If True, check if adding this dependent would create a cycle.

        Raises:
            GraphCycleError: If check_cycles is True and a cycle would be created.
        """
        if check_cycles:
            logger.debug(
                f"Checking if adding dependent '{dependent.reference}' to '{self.reference}' creates a cycle"
            )
            if path := dependent.find_path(self):
                cycle = path + [dependent]
                logger.error(
                    f"Cycle detected: {' -> '.join(str(n.reference) for n in cycle)}"
                )
                raise GraphCycleError(
                    f"Adding dependent '{dependent.reference}' to "
                    f"'{self.reference}' would create a cycle.",
                    cycle=cycle,
                )

        logger.debug(
            f"Node '{self.reference}': adding dependent '{dependent.reference}'"
        )
        self._add_dependent(dependent)
        dependent._add_depends_on(self)

    def add_dependents(self, dependents: set[Self], check_cycles: bool = False) -> None:
        """
        Add multiple dependents to this node.

        Args:
            dependents (set[Self]): A set of Graphable nodes to add as dependents.
            check_cycles (bool): If True, check if adding these dependents would create a cycle.
        """
        logger.debug(f"Node '{self.reference}': adding dependents {dependents}")
        for dependent in dependents:
            self.add_dependent(dependent, check_cycles=check_cycles)

    def _add_dependent(self, dependent: Self) -> None:
        """
        Internal method to add a dependent node (incoming edge in dependency graph).

        Args:
            dependent (Self): The node that depends on this node.
        """
        if dependent not in self._dependents:
            self._dependents.add(dependent)
            logger.debug(
                f"Node '{self.reference}': added dependent '{dependent.reference}'"
            )
            self._notify_change()

    def _add_depends_on(self, depends_on: Self) -> None:
        """
        Internal method to add a dependency (outgoing edge in dependency graph).

        Args:
            depends_on (Self): The node that this node depends on.
        """
        if depends_on not in self._depends_on:
            self._depends_on.add(depends_on)
            logger.debug(
                f"Node '{self.reference}': added dependency '{depends_on.reference}'"
            )
            self._notify_change()

    def _remove_dependent(self, dependent: Self) -> None:
        """
        Internal method to remove a dependent node.

        Args:
            dependent (Self): The node to remove.
        """
        if dependent in self._dependents:
            self._dependents.remove(dependent)
            logger.debug(
                f"Node '{self.reference}': removed dependent '{dependent.reference}'"
            )
            self._notify_change()

    def _remove_depends_on(self, depends_on: Self) -> None:
        """
        Internal method to remove a dependency.

        Args:
            depends_on (Self): The node to remove.
        """
        if depends_on in self._depends_on:
            self._depends_on.remove(depends_on)
            logger.debug(
                f"Node '{self.reference}': removed dependency '{depends_on.reference}'"
            )
            self._notify_change()

    def _register_observer(self, observer: Any) -> None:
        """Register an observer to be notified of changes."""
        self._observers.add(observer)

    def _unregister_observer(self, observer: Any) -> None:
        """Unregister an observer."""
        self._observers.discard(observer)

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to this node.

        Args:
            tag (str): The tag to add.
        """
        self._tags.add(tag)
        logger.debug(f"Added tag '{tag}' to {self.reference}")
        self._notify_change()

    @property
    def dependents(self) -> set[Self]:
        """
        Get the set of nodes that depend on this node.

        Returns:
            set[Self]: A copy of the dependents set.
        """
        return cast(set[Self], set(self._dependents))

    @property
    def depends_on(self) -> set[Self]:
        """
        Get the set of nodes that this node depends on.

        Returns:
            set[Self]: A copy of the dependencies set.
        """
        return cast(set[Self], set(self._depends_on))

    def is_tagged(self, tag: str) -> bool:
        """
        Check if the node has a specific tag.

        Args:
            tag (str): The tag to check.

        Returns:
            bool: True if the tag exists, False otherwise.
        """
        logger.debug(f"Node '{self.reference}': checking if tagged with '{tag}'")
        return tag in self._tags

    def find_path(self, target: Self) -> list[Self] | None:
        """
        Find a path from this node to the target node using BFS.

        Args:
            target (Self): The target node to find a path to.

        Returns:
            list[Self] | None: The shortest path as a list of nodes, or None if no path exists.
        """
        logger.debug(
            f"Searching for path from '{self.reference}' to '{target.reference}'"
        )
        queue: deque[tuple[Self, list[Self]]] = deque()
        for neighbor in self._dependents:
            # neighbor is Graphable[Any], Self is a bound of Graphable[T]
            queue.append((cast(Self, neighbor), [self, cast(Self, neighbor)]))

        visited: set[Graphable[Any]] = set()
        while queue:
            current, path = queue.popleft()
            if current == target:
                logger.debug(
                    f"Path found: {' -> '.join(str(n.reference) for n in path)}"
                )
                return path

            if current in visited:
                continue

            visited.add(current)
            for neighbor in current.dependents:
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        logger.debug(f"No path found from '{self.reference}' to '{target.reference}'")
        return None

    def provides_to(self, dependent: Self, check_cycles: bool = False) -> None:
        """
        Alias for add_dependent: indicates this node provides something to another.

        Args:
            dependent (Self): The Graphable node that receives the provision.
            check_cycles (bool): If True, check if adding this dependent would create a cycle.
        """
        logger.debug(
            f"Node '{self.reference}': providing to '{dependent.reference}' (via alias)"
        )
        self.add_dependent(dependent, check_cycles=check_cycles)

    @property
    def reference(self) -> T:
        """
        Get the underlying reference object.

        Returns:
            T: The reference object.
        """
        return self._reference

    def requires(self, dependency: Self, check_cycles: bool = False) -> None:
        """
        Alias for add_dependency: indicates this node requires another node.

        Args:
            dependency (Self): The Graphable node that is required.
            check_cycles (bool): If True, check if adding this dependency would create a cycle.
        """
        logger.debug(
            f"Node '{self.reference}': requiring dependency '{dependency.reference}' (via alias)"
        )
        self.add_dependency(dependency, check_cycles=check_cycles)

    @property
    def tags(self) -> set[str]:
        """
        Get the set of tags for this node.

        Returns:
            set[str]: A copy of the tags set.
        """
        return set(self._tags)

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from this node.

        Args:
            tag (str): The tag to remove.
        """
        if tag in self._tags:
            self._tags.discard(tag)
            logger.debug(f"Removed tag '{tag}' from {self.reference}")
            self._notify_change()
