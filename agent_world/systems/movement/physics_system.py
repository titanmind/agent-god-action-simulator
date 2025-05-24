"""Integrate forces into velocity and resolve simple collisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .pathfinding import is_blocked
from ...core.components.position import Position
from ...core.components.physics import Physics


@dataclass
class Force:
    """Instantaneous force applied to an entity for one tick."""

    fx: float
    fy: float


class PhysicsSystem:
    """Update :class:`Physics` components from accumulated :class:`Force` values."""

    def __init__(self, world: Any) -> None:
        self.world = world

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Integrate forces and zero velocity on collisions."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        size = getattr(self.world, "size", (0, 0))
        if em is None or cm is None:
            return

        width, height = size
        for entity_id in list(em.all_entities.keys()):
            phys = cm.get_component(entity_id, Physics)
            if phys is None:
                continue

            force = cm.get_component(entity_id, Force)
            if force is not None:
                phys.vx += force.fx / phys.mass
                phys.vy += force.fy / phys.mass
                cm.remove_component(entity_id, Force)

            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue

            next_x = pos.x + int(round(phys.vx))
            next_y = pos.y + int(round(phys.vy))
            if (
                next_x < 0
                or next_x >= width
                or next_y < 0
                or next_y >= height
                or is_blocked((next_x, next_y))
            ):
                phys.vx = 0.0
                phys.vy = 0.0


__all__ = ["Force", "PhysicsSystem"]
