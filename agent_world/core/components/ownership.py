"""Ownership component."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Ownership:
    """Record the owning entity ID for another entity."""

    owner_id: int


__all__ = ["Ownership"]
