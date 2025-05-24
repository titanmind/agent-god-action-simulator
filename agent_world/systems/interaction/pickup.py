"""Item pickup system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.components.position import Position
from ...core.components.inventory import Inventory


@dataclass
class Tag:
    """Simple tag component used for categorising entities."""

    name: str


class PickupSystem:
    """Move co-located item entities into inventories."""

    def __init__(self, world: Any) -> None:
        self.world = world

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Transfer items found at the same position into inventories."""

        if self.world.entity_manager is None or self.world.component_manager is None:
            return

        em = self.world.entity_manager
        cm = self.world.component_manager

        # Iterate over actors that can carry items
        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            inv = cm.get_component(entity_id, Inventory)
            if pos is None or inv is None:
                continue

            # Look for items occupying the same position
            for other_id in list(em.all_entities.keys()):
                if other_id == entity_id:
                    continue
                other_pos = cm.get_component(other_id, Position)
                if other_pos is None or (other_pos.x, other_pos.y) != (pos.x, pos.y):
                    continue

                tag = cm.get_component(other_id, Tag)
                if tag is None or tag.name != "item":
                    continue

                if len(inv.items) >= inv.capacity:
                    continue

                inv.items.append(other_id)
                em.destroy_entity(other_id)
                cm.remove_component(other_id, Position)
                cm.remove_component(other_id, Tag)
