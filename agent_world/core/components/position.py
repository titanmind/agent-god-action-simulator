"""Position component."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position:
    """Simple 2D coordinate."""

    x: int
    y: int


__all__ = ["Position"]
