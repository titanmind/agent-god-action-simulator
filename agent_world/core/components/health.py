"""Health component."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Health:
    """Track current and maximum health."""

    cur: int
    max: int


__all__ = ["Health"]
