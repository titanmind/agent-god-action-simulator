"""Movement system handling basic velocity-based translation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.components.position import Position


@dataclass
class Velocity:
    """Per-tick delta movement for an entity."""

    dx: int
    dy: int


class MovementSystem:
    """Update entity positions based on attached :class:`Velocity`."""

    def __init__(self, world: Any) -> None:
        self.world = world

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Move all entities with ``Position`` and ``Velocity`` components."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        index = getattr(self.world, "spatial_index", None)
        if em is None or cm is None or index is None:
            return

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            vel = cm.get_component(entity_id, Velocity)
            if pos is None or vel is None:
                continue

            old_pos = (pos.x, pos.y)
            pos.x += vel.dx
            pos.y += vel.dy

            if old_pos != (pos.x, pos.y):
                index.remove(entity_id)
                index.insert(entity_id, (pos.x, pos.y))


__all__ = ["Velocity", "MovementSystem"]
