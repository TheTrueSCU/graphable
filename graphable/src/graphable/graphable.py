from typing import Any


class Graphable[T, S: Graphable[Any, Any]]:
    def __init__(self, reference: T):
        self._dependents: set[S] = set()
        self._depends_on: set[S] = set()
        self._reference: T = reference

    def _add_dependent(self, dependent: S) -> None:
        self._dependents.add(dependent)

    def _add_depends_on(self, depends_on: S) -> None:
        self._depends_on.add(depends_on)

    @property
    def dependents(self) -> set[S]:
        return set(self._dependents)

    @property
    def depends_on(self) -> set[S]:
        return set(self._depends_on)

    @property
    def reference(self) -> T:
        return self._reference
