from __future__ import annotations

"""Built-in melee attack ability."""

from typing import Any, Optional

from agent_world.abilities.base import Ability
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.combat.combat_system import CombatSystem


class MeleeStrike(Ability):
    """Basic melee attack targeting the first enemy in range."""

    def __init__(self) -> None:
        self.target: Optional[int] = None

    # ------------------------------------------------------------------
    # Ability interface
    # ------------------------------------------------------------------
    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> int:
        return 1

    def can_use(self, caster_id: int, world: Any) -> bool:
        """Return ``True`` if any target is within melee range."""

        if (
            getattr(world, "entity_manager", None) is None
            or getattr(world, "component_manager", None) is None
        ):
            return False

        em = world.entity_manager
        cm = world.component_manager
        pos = cm.get_component(caster_id, Position)
        if pos is None:
            return False

        for ent in em.all_entities.keys():
            if ent == caster_id:
                continue
            tpos = cm.get_component(ent, Position)
            hp = cm.get_component(ent, Health)
            if tpos is None or hp is None or hp.cur <= 0:
                continue
            if CombatSystem._in_melee_range(pos, tpos):
                self.target = ent
                return True
        return False

    def execute(self, caster_id: int, world: Any) -> None:
        """Perform a melee strike against the selected target."""

        if self.target is None:
            return

        combat = CombatSystem(world)
        combat.attack(caster_id, self.target)
        self.target = None


__all__ = ["MeleeStrike"]
