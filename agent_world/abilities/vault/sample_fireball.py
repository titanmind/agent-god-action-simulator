from __future__ import annotations

"""Sample fireball ability for tests."""

from typing import Any, Optional

from agent_world.abilities.base import Ability

METADATA = {
    "tags": ["fireball", "fire", "ranged"],
    "description": "simple fireball ability",
}


class SampleFireball(Ability):
    """Minimal fireball that prints output."""

    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> int:
        return 1

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
        return True

    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
        print(f"[SampleFireball] Agent {caster_id} throws a fireball at {target_id}!")


__all__ = ["SampleFireball"]
