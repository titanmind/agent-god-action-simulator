from __future__ import annotations

"""Built-in ranged combat ability."""

from typing import Any, Optional

from agent_world.abilities.base import Ability
from agent_world.core.components.position import Position
from agent_world.core.components.inventory import Inventory
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.systems.perception.line_of_sight import has_line_of_sight

class ArrowShot(Ability):
    """Shoot the nearest visible target and consume one ammo item."""

    def __init__(self, range: int = 5) -> None:
        self.range = range
        self._target: Optional[int] = None

    # ------------------------------------------------------------------
    # Ability metadata
    # ------------------------------------------------------------------
    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> int:
        return 2

    # ------------------------------------------------------------------
    # Usage checks
    # ------------------------------------------------------------------
    def can_use(self, caster_id: int, world: Any) -> bool:
        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None or not em.has_entity(caster_id):
            return False

        pos = cm.get_component(caster_id, Position)
        inv = cm.get_component(caster_id, Inventory)
        if pos is None or inv is None or not inv.items:
            return False

        for ent in list(em.all_entities.keys()):
            if ent == caster_id:
                continue
            other_pos = cm.get_component(ent, Position)
            if other_pos is None:
                continue
            if has_line_of_sight(pos, other_pos, self.range):
                self._target = ent
                return True
        return False

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def execute(self, caster_id: int, world: Any) -> None:
        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None or not em.has_entity(caster_id):
            return

        inv = cm.get_component(caster_id, Inventory)
        pos = cm.get_component(caster_id, Position)
        if inv is None or pos is None or not inv.items:
            return

        target = self._target
        if target is None or not em.has_entity(target):
            # Acquire a new target if cached one is invalid
            for ent in list(em.all_entities.keys()):
                if ent == caster_id:
                    continue
                other_pos = cm.get_component(ent, Position)
                if other_pos is None:
                    continue
                if has_line_of_sight(pos, other_pos, self.range):
                    target = ent
                    break
        if target is None:
            return

        inv.items.pop(0)
        CombatSystem(world).attack(caster_id, target)
        self._target = None


__all__ = ["ArrowShot"]
