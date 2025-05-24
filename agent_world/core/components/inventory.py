"""Inventory component."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Inventory:
    """Container for carrying items."""

    capacity: int
    items: List[Any] = field(default_factory=list)


__all__ = ["Inventory"]
