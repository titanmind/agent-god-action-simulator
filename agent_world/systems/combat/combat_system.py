"""Basic melee combat system."""

from __future__ import annotations

import random
from typing import Any, Dict, List

from ...core.components.position import Position
from ...core.components.health import Health
from ..combat.damage_types import DamageType
from ..combat.defense import Defense, armor_vs, dodge_vs
from ...persistence.event_log import (
    append_event,
    COMBAT_ATTACK,
    COMBAT_DEATH,
)
from pathlib import Path


class CombatSystem:
    """Handle simple melee attacks between entities."""

    def __init__(self, world: Any, event_log: list[dict[str, Any]] | None = None) -> None:  # noqa: D401
        self.world = world

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

        dest = getattr(self.world, "persistent_event_log_path", None)
        if dest is None:
            dest = Path("persistent_events.log")
            setattr(self.world, "persistent_event_log_path", dest)

        tick_val = tick
        if tick_val is None:
            tick_val = getattr(getattr(self.world, "time_manager", None), "tick_counter", 0)

        data: Dict[str, Any] = {
            "attacker": attacker,
            "target": target,
            "damage": damage,
            "damage_type": damage_type.name,
        }
        if dodged:
            data["dodged"] = True
        append_event(dest, tick_val, COMBAT_ATTACK, data)

        if hp.cur <= 0:
            death_data = {"entity": target, "killer": attacker}
            append_event(dest, tick_val, COMBAT_DEATH, death_data)
        return True


__all__ = ["CombatSystem"]
