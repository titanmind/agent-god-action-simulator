"""Simple barter system for exchanging inventory items."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from .pickup import Tag

# ----------------------------------------------------------------------
# Dynamic pricing helpers
# ----------------------------------------------------------------------
# Simple default base values for each known tradable.
BASE_VALUES: Dict[str, int] = {
    "ore": 10,
    "wood": 5,
    "herbs": 8,
    "item": 4,
}


def _count_resources(world: Any, kind: str, pos: Tuple[int, int], radius: int) -> int:
    """Return number of resource tiles of ``kind`` within ``radius`` of ``pos``."""

    tile_map = getattr(world, "tile_map", None)
    if not tile_map:
        return 0

    width = len(tile_map[0])
    height = len(tile_map)
    x0 = max(0, pos[0] - radius)
    x1 = min(width - 1, pos[0] + radius)
    y0 = max(0, pos[1] - radius)
    y1 = min(height - 1, pos[1] + radius)

    count = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            tile = tile_map[y][x]
            if tile and tile.get("kind") == kind:
                count += 1
    return count


def _count_items(world: Any, pos: Tuple[int, int], radius: int) -> int:
    """Return number of item entities within ``radius`` of ``pos``."""

    spatial = getattr(world, "spatial_index", None)
    cm = getattr(world, "component_manager", None)
    if spatial is None or cm is None:
        return 0

    count = 0
    for ent in spatial.query_radius(pos, radius):
        tag = cm.get_component(ent, Tag)
        if tag is not None and tag.name == "item":
            count += 1
    return count


def get_local_prices(
    world: Any, pos: Tuple[int, int], radius: int = 10
) -> Dict[str, float]:
    """Return dynamic prices around ``pos``.

    Prices start from ``BASE_VALUES`` and decrease with local supply.
    """

    prices: Dict[str, float] = {}

    for kind, base in BASE_VALUES.items():
        if kind == "item":
            supply = _count_items(world, pos, radius)
        else:
            supply = _count_resources(world, kind, pos, radius)
        prices[kind] = base / (1 + supply)

    return prices


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


__all__ = ["TradingSystem", "get_local_prices"]
