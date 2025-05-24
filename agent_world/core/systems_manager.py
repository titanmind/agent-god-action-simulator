"""System registry and tick dispatcher."""

from __future__ import annotations

from typing import Any, Iterable, List

from agent_world.systems.movement.movement_system import MovementSystem
from agent_world.systems.movement.physics_system import PhysicsSystem


class SystemsManager:
    """Maintain an ordered list of systems and tick them sequentially."""

    def __init__(self) -> None:
        self._systems: List[Any] = []

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------
    def register(self, system: Any) -> None:
        """Add ``system`` to the update list if not already present.

        Ensures that :class:`PhysicsSystem` always runs before
        :class:`MovementSystem` regardless of registration order.
        """

        if system in self._systems:
            return

        if isinstance(system, PhysicsSystem):
            for idx, s in enumerate(self._systems):
                if isinstance(s, MovementSystem):
                    self._systems.insert(idx, system)
                    break
            else:
                self._systems.append(system)
            return

        if isinstance(system, MovementSystem):
            for idx, s in enumerate(self._systems):
                if isinstance(s, PhysicsSystem):
                    # insert after existing physics system
                    self._systems.insert(idx + 1, system)
                    break
            else:
                self._systems.append(system)
            return

        self._systems.append(system)

    def unregister(self, system: Any) -> None:
        """Remove ``system`` if currently registered."""

        if system in self._systems:
            self._systems.remove(system)

    # ------------------------------------------------------------------
    # Tick dispatch
    # ------------------------------------------------------------------
    def update(self, *args: Any, **kwargs: Any) -> None:
        """Call ``update`` on each registered system in order."""

        for system in list(self._systems):
            update = getattr(system, "update", None)
            if callable(update):
                update(*args, **kwargs)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def __iter__(self) -> Iterable[Any]:
        return iter(self._systems)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._systems)


__all__ = ["SystemsManager"]
