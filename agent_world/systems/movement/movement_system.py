"""Movement system handling basic velocity-based translation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .pathfinding import is_blocked

from ...core.components.position import Position
from ...core.components.physics import Physics


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
        """Move all entities with ``Position`` and a velocity source."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        index = getattr(self.world, "spatial_index", None)
        size = getattr(self.world, "size", (0, 0))
        if em is None or cm is None or index is None:
            return

        batch: list[tuple[int, tuple[int, int]]] = []
        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            vel = cm.get_component(entity_id, Velocity)
            phys = cm.get_component(entity_id, Physics)
            if pos is None or (vel is None and phys is None):
                continue

            old_pos = (pos.x, pos.y)

            if vel is not None:
                dx, dy = vel.dx, vel.dy
            else:
                dx = int(round(phys.vx))
                dy = int(round(phys.vy))
                phys.vx *= phys.friction
                phys.vy *= phys.friction

            new_x = pos.x + dx
            new_y = pos.y + dy
            width, height = size
            if (
                0 <= new_x < width
                and 0 <= new_y < height
                and not is_blocked((new_x, new_y))
            ):
                pos.x = new_x
                pos.y = new_y

            if old_pos != (pos.x, pos.y):
                index.remove(entity_id)
                batch.append((entity_id, (pos.x, pos.y)))

        if batch:
            index.insert_many(batch)


__all__ = ["Velocity", "MovementSystem"]
