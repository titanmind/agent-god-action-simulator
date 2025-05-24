"""Event dataclasses used by core systems."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AbilityUseEvent:
    """Record that an ability was used by an entity."""

    caster_id: int
    ability_name: str
    target_id: int | None
    tick: int


__all__ = ["AbilityUseEvent"]
