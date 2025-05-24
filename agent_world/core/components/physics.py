"""Basic physics component."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Physics:
    """Simple physics attributes for an entity."""

    mass: float
    vx: float
    vy: float
    friction: float


__all__ = ["Physics"]
