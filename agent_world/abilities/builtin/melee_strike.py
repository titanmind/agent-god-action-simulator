from __future__ import annotations

"""Minimal melee attack ability."""

from typing import Any, Optional

from agent_world.abilities.base import Ability
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.combat.combat_system import CombatSystem


class MeleeStrike(Ability):
    """Perform a basic adjacent attack."""

    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> int:
        return 1

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None or target_id is None:
            return False
        if not em.has_entity(caster_id) or not em.has_entity(target_id):
            return False
        caster_pos = cm.get_component(caster_id, Position)
        target_pos = cm.get_component(target_id, Position)
        target_hp = cm.get_component(target_id, Health)
        if caster_pos is None or target_pos is None or target_hp is None or target_hp.cur <= 0:
            return False
        return CombatSystem._in_melee_range(caster_pos, target_pos)

    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
        if not self.can_use(caster_id, world, target_id):
            return
        CombatSystem(world).attack(caster_id, target_id)  # type: ignore[arg-type]


__all__ = ["MeleeStrike"]
