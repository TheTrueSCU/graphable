from logging import getLogger
from typing import cast

logger = getLogger(__name__)


class Graphable[T, S: Graphable[T, S]]:
    """
    A generic class representing a node in a graph that can track dependencies and dependents.

    Type Parameters:
        T: The type of the reference object this node holds.
        S: The type of the Graphable subclass (recursive bound).
    """

    def __init__(self, reference: T):
        """
        Initialize a Graphable node.

        Args:
            reference (T): The underlying object this node represents.
        """
        self._dependents: set[S] = set()
        self._depends_on: set[S] = set()
        self._reference: T = reference
        self._tags: set[str] = set()
        logger.debug(f"Created Graphable node for reference: {reference}")

    def _add_dependent(self, dependent: S) -> None:
        """
        Internal method to add a dependent node (incoming edge in dependency graph).

        Args:
            dependent (S): The node that depends on this node.
        """
        if dependent not in self._dependents:
            self._dependents.add(dependent)
            logger.debug(
                f"Node '{self.reference}': added dependent '{cast(Graphable, dependent).reference}'"
            )

    def _add_depends_on(self, depends_on: S) -> None:
        """
        Internal method to add a dependency (outgoing edge in dependency graph).

        Args:
            depends_on (S): The node that this node depends on.
        """
        if depends_on not in self._depends_on:
            self._depends_on.add(depends_on)
            logger.debug(
                f"Node '{self.reference}': added dependency '{cast(Graphable, depends_on).reference}'"
            )

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to this node.

        Args:
            tag (str): The tag to add.
        """
        self._tags.add(tag)
        logger.debug(f"Added tag '{tag}' to {self.reference}")

    @property
    def dependents(self) -> set[S]:
        """
        Get the set of nodes that depend on this node.

        Returns:
            set[S]: A copy of the dependents set.
        """
        return set(self._dependents)

    @property
    def depends_on(self) -> set[S]:
        """
        Get the set of nodes that this node depends on.

        Returns:
            set[S]: A copy of the dependencies set.
        """
        return set(self._depends_on)

    def is_tagged(self, tag: str) -> bool:
        """
        Check if the node has a specific tag.

        Args:
            tag (str): The tag to check.

        Returns:
            bool: True if the tag exists, False otherwise.
        """
        return tag in self._tags

    @property
    def reference(self) -> T:
        """
        Get the underlying reference object.

        Returns:
            T: The reference object.
        """
        return self._reference

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
        self._tags.discard(tag)
        logger.debug(f"Removed tag '{tag}' from {self.reference}")
