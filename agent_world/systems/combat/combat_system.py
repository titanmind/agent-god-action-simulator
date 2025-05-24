"""Basic melee combat system."""

from __future__ import annotations

from typing import Any, List, Dict

from ...core.components.position import Position
from ...core.components.health import Health
from ..combat.damage_types import DamageType


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

        hp.cur = max(hp.cur - 10, 0)

        event = {
            "type": "attack",
            "attacker": attacker,
            "target": target,
            "damage": 10,
            "damage_type": damage_type.name,
        }
        if tick is not None:
            event["tick"] = tick
        self.event_log.append(event)
        return True


__all__ = ["CombatSystem"]
