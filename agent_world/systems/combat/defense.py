"""Defense component helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .damage_types import DamageType


@dataclass
class Defense:
    """Per-damage-type armor and dodge chances."""

    armor: Dict[DamageType, int] = field(
        default_factory=lambda: {dt: 0 for dt in DamageType}
    )
    dodge: Dict[DamageType, float] = field(
        default_factory=lambda: {dt: 0.0 for dt in DamageType}
    )


def armor_vs(defense: Defense, damage_type: DamageType) -> int:
    """Return armor value against ``damage_type``."""

    return defense.armor.get(damage_type, 0)


def dodge_vs(defense: Defense, damage_type: DamageType) -> float:
    """Return dodge chance against ``damage_type``."""

    return defense.dodge.get(damage_type, 0.0)


__all__ = ["Defense", "armor_vs", "dodge_vs"]

