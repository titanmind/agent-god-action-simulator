"""Stealing system with reputation penalties."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.components.position import Position
from ...core.components.inventory import Inventory


try:  # Relationship component may not yet exist
    from ...core.components.relationship import Relationship  # type: ignore
except Exception:  # pragma: no cover - fallback definition for tests

    @dataclass
    class Relationship:
        faction: str = ""
        reputation: int = 0


class StealingSystem:
    """Allow entities to steal items and lose reputation."""

    def __init__(self, world: Any, penalty: int = 1) -> None:
        self.world = world
        self.penalty = penalty

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Move one item from victim to thief if co-located."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        if em is None or cm is None:
            return

        entities = list(em.all_entities.keys())
        for thief_id in entities:
            pos_t = cm.get_component(thief_id, Position)
            inv_t = cm.get_component(thief_id, Inventory)
            if pos_t is None or inv_t is None:
                continue
            if len(inv_t.items) >= inv_t.capacity:
                continue

            for victim_id in entities:
                if victim_id == thief_id:
                    continue
                pos_v = cm.get_component(victim_id, Position)
                inv_v = cm.get_component(victim_id, Inventory)
                if (
                    pos_v is None
                    or inv_v is None
                    or not inv_v.items
                    or (pos_v.x, pos_v.y) != (pos_t.x, pos_t.y)
                ):
                    continue

                inv_t.items.append(inv_v.items.pop(0))
                rel = cm.get_component(thief_id, Relationship)
                if rel is not None and hasattr(rel, "reputation"):
                    rel.reputation -= self.penalty
                return


__all__ = ["StealingSystem", "Relationship"]
