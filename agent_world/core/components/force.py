"""Force/impulse component for physics integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Force:
    """Directional impulse applied over multiple ticks."""

    dx: float
    dy: float
    ttl: int = 1


def apply_force(world: Any, entity_id: int, dx: float, dy: float, ttl: int = 1) -> None:
    """Attach or accumulate a :class:`Force` on ``entity_id``."""

    cm = getattr(world, "component_manager", None)
    if cm is None:
        return

    existing = cm.get_component(entity_id, Force)
    if existing is None:
        cm.add_component(entity_id, Force(dx, dy, ttl))
    else:
        existing.dx += dx
        existing.dy += dy
        existing.ttl = max(existing.ttl, ttl)


__all__ = ["Force", "apply_force"]
