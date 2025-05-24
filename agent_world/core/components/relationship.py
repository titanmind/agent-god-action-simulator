"""Relationship component."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Relationship:
    """Track faction affiliation and reputation."""

    faction: str = ""
    reputation: int = 0


__all__ = ["Relationship"]
