"""Simple barter system for exchanging inventory items."""

from __future__ import annotations

from typing import Any

from ...core.components.position import Position
from ...core.components.inventory import Inventory


class TradingSystem:
    """Swap the first item between co-located inventories."""

    def __init__(self, world: Any) -> None:
        self.world = world

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
                return


__all__ = ["TradingSystem"]
