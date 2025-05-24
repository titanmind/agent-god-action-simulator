"""Item pickup system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.components.position import Position
from ...core.components.inventory import Inventory
from ...core.components.ownership import Ownership


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

        if (
            self.world.entity_manager is None
            or self.world.component_manager is None
            or self.world.spatial_index is None
        ):
            return

        em = self.world.entity_manager
        cm = self.world.component_manager
        index = self.world.spatial_index

        # Iterate over actors that can carry items
        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            inv = cm.get_component(entity_id, Inventory)
            if pos is None or inv is None:
                continue

            # Look for items occupying the same position
            for other_id in index.query_radius((pos.x, pos.y), 0):
                if other_id == entity_id:
                    continue

                tag = cm.get_component(other_id, Tag)
                if tag is None or tag.name != "item":
                    continue

                if len(inv.items) >= inv.capacity:
                    continue

                # Copy or assign ownership to the item
                ownership = cm.get_component(other_id, Ownership)
                if ownership is None:
                    cm.add_component(other_id, Ownership(owner_id=entity_id))
                else:
                    ownership.owner_id = entity_id

                inv.items.append(other_id)
                em.destroy_entity(other_id)
                cm.remove_component(other_id, Position)
                cm.remove_component(other_id, Tag)
                index.remove(other_id)
