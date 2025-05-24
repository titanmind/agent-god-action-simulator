"""Damage type definitions."""

from __future__ import annotations

from enum import Enum


class DamageType(Enum):
    """Enumerate supported damage categories."""

    MELEE = "melee"


__all__ = ["DamageType"]
