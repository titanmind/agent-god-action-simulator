"""Basic melee combat system."""

from __future__ import annotations

import random
from typing import Any, List, Dict

from ...core.components.position import Position
from ...core.components.health import Health
from ..combat.damage_types import DamageType
from ..combat.defense import Defense, armor_vs, dodge_vs


class CombatSystem:
    """Handle simple melee attacks between entities."""

    def __init__(self, world: Any, event_log: List[Dict[str, Any]] | None = None) -> None:
        self.world = world
        self.event_log = event_log if event_log is not None else []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _in_melee_range(a: Position, b: Position) -> bool:
        """Return ``True`` if two positions are within melee range (1 tile)."""
        dx = a.x - b.x
        dy = a.y - b.y
        return dx * dx + dy * dy <= 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def attack(
        self,
        attacker: int,
        target: int,
        damage_type: DamageType = DamageType.MELEE,
        tick: int | None = None,
    ) -> bool:
        """Perform a melee attack from ``attacker`` to ``target``."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        if em is None or cm is None:
            return False

        if not em.has_entity(attacker) or not em.has_entity(target):
            return False

        pos_a = cm.get_component(attacker, Position)
        pos_t = cm.get_component(target, Position)
        if pos_a is None or pos_t is None:
            return False

        if not self._in_melee_range(pos_a, pos_t):
            return False

        hp = cm.get_component(target, Health)
        if hp is None:
            return False

        base_damage = 10
        defense = cm.get_component(target, Defense)
        dodged = False
        if defense is not None and random.random() < dodge_vs(defense, damage_type):
            damage = 0
            dodged = True
        else:
            armor = armor_vs(defense, damage_type) if defense is not None else 0
            damage = max(base_damage - armor, 0)

        hp.cur = max(hp.cur - damage, 0)

        event = {
            "type": "attack",
            "attacker": attacker,
            "target": target,
            "damage": damage,
            "damage_type": damage_type.name,
        }
        if dodged:
            event["dodged"] = True
        if tick is not None:
            event["tick"] = tick
        self.event_log.append(event)

        if hp.cur <= 0:
            death_event = {"type": "death", "entity": target, "killer": attacker}
            if tick is not None:
                death_event["tick"] = tick
            self.event_log.append(death_event)
        return True


__all__ = ["CombatSystem"]
