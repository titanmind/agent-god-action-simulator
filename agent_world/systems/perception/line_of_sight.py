"""Line-of-sight helpers."""

from __future__ import annotations

from agent_world.core.components.position import Position


def has_line_of_sight(a: Position, b: Position, max_distance: int) -> bool:
    """Return ``True`` if ``a`` can see ``b`` within ``max_distance``."""

    dx = a.x - b.x
    dy = a.y - b.y
    return dx * dx + dy * dy <= max_distance * max_distance


__all__ = ["has_line_of_sight"]
