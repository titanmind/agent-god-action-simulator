"""Basic inventory crafting system using JSON recipes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ...core.components.inventory import Inventory
from ...core.components.ownership import Ownership
from ...persistence.event_log import append_event, CRAFT


class CraftingSystem:
    """Consume items from inventories to produce new ones."""

    def __init__(
        self,
        world: Any,
        recipe_path: str | Path | None = None,
        event_log: list[dict[str, Any]] | None = None,
    ) -> None:
        self.world = world
        if recipe_path is None:
            recipe_path = (
                Path(__file__).resolve().parents[2] / "data" / "recipes.json"
            )
        self.recipes = self._load_recipes(recipe_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_recipes(path: str | Path) -> Dict[str, Dict[str, int]]:
        """Return recipe table loaded from ``path``."""

        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}

        recipes: Dict[str, Dict[str, int]] = {}
        for key, val in data.items():
            inputs = int(val.get("inputs", 0))
            outputs = int(val.get("outputs", 0))
            recipes[str(key)] = {"inputs": inputs, "outputs": outputs}
        return recipes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def craft(self, entity_id: int, recipe_id: str | int) -> bool:
        """Craft ``recipe_id`` for ``entity_id`` if resources allow."""

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        if em is None or cm is None:
            return False

        recipe = self.recipes.get(str(recipe_id))
        if recipe is None:
            return False

        inv = cm.get_component(entity_id, Inventory)
        if inv is None or len(inv.items) < recipe["inputs"]:
            return False

        consumed: List[int] = [inv.items.pop(0) for _ in range(recipe["inputs"])]
        produced: List[int] = []
        for _ in range(recipe["outputs"]):
            item_id = em.create_entity()
            cm.add_component(item_id, Ownership(owner_id=entity_id))
            inv.items.append(item_id)
            produced.append(item_id)

        dest = getattr(self.world, "persistent_event_log_path", None)
        if dest is None:
            dest = Path("persistent_events.log")
            setattr(self.world, "persistent_event_log_path", dest)

        tick = getattr(getattr(self.world, "time_manager", None), "tick_counter", 0)

        data = {
            "entity": entity_id,
            "recipe": recipe_id,
            "consumed": consumed,
            "produced": produced,
        }
        append_event(dest, tick, CRAFT, data)
        return True


__all__ = ["CraftingSystem"]
