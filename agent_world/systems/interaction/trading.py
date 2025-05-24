"""Simple barter system for exchanging inventory items."""

from __future__ import annotations

from typing import Any

from ...core.components.position import Position
from ...core.components.inventory import Inventory

try:  # Relationship component may not yet exist
    from ...core.components.relationship import Relationship  # type: ignore
except Exception:  # pragma: no cover - fallback for tests

    class Relationship:  # type: ignore
        reputation: int = 0


class TradingSystem:
    """Swap the first item between co-located inventories and reward traders."""

    def __init__(self, world: Any, reward: int = 1) -> None:
        self.world = world
        self.reward = reward

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Perform a single barter between nearby entities."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        if em is None or cm is None:
            return

        entities = list(em.all_entities.keys())

        for i, a in enumerate(entities):
            pos_a = cm.get_component(a, Position)
            inv_a = cm.get_component(a, Inventory)
            if pos_a is None or inv_a is None or not inv_a.items:
                continue

            for b in entities[i + 1 :]:
                pos_b = cm.get_component(b, Position)
                inv_b = cm.get_component(b, Inventory)
                if (
                    pos_b is None
                    or inv_b is None
                    or not inv_b.items
                    or (pos_a.x, pos_a.y) != (pos_b.x, pos_b.y)
                ):
                    continue

                item_a = inv_a.items.pop(0)
                item_b = inv_b.items.pop(0)
                inv_a.items.append(item_b)
                inv_b.items.append(item_a)
                rel_a = cm.get_component(a, Relationship)
                if rel_a is not None and hasattr(rel_a, "reputation"):
                    rel_a.reputation += self.reward
                rel_b = cm.get_component(b, Relationship)
                if rel_b is not None and hasattr(rel_b, "reputation"):
                    rel_b.reputation += self.reward
                return


__all__ = ["TradingSystem"]
