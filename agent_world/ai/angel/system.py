"""Angel system for granting new abilities."""

from __future__ import annotations

from typing import Any
import re

from . import generator as angel_generator
from .vault_index import get_vault_index
from ...core.components.known_abilities import KnownAbilitiesComponent


class AngelSystem:
    """Generate abilities via Vault lookup or LLM."""

    def __init__(self, world: Any) -> None:
        self.world = world

    def _grant_to_agent(self, agent_id: int, class_name: str) -> None:
        cm = getattr(self.world, "component_manager", None)
        if cm is None:
            return
        comp = cm.get_component(agent_id, KnownAbilitiesComponent)
        if comp is None:
            comp = KnownAbilitiesComponent()
            cm.add_component(agent_id, comp)
        if class_name not in comp.known_class_names:
            comp.known_class_names.append(class_name)

    def generate_and_grant(self, agent_id: int, description: str) -> dict:
        """Generate an ability or fetch one from the vault."""
        if getattr(self.world, "component_manager", None) is None:
            # Stub path for early tests when world is not fully initialized
            return {"status": "stub"}
        vault_match = get_vault_index().lookup(description)
        if vault_match:
            self._grant_to_agent(agent_id, vault_match)
            return {"status": "success", "ability_class_name": vault_match}

        llm = getattr(self.world, "llm_manager_instance", None)
        if llm is not None:
            llm.request(f"Generate ability code for: {description}")

        path = angel_generator.generate_ability(description)
        class_name = None
        try:
            text = path.read_text(encoding="utf-8")
            m = re.search(r"class\s+(\w+)\s*\(Ability\)", text)
            if m:
                class_name = m.group(1)
        except Exception:
            pass
        if class_name is None:
            slug = angel_generator._slugify(description)
            class_name = angel_generator._class_name_from_slug(slug)
        self._grant_to_agent(agent_id, class_name)
        return {"status": "success", "ability_class_name": class_name}


def get_angel_system(world: Any) -> AngelSystem:
    """Return existing AngelSystem instance on world or create one."""
    if not hasattr(world, "angel_system_instance") or world.angel_system_instance is None:
        world.angel_system_instance = AngelSystem(world)
    return world.angel_system_instance


__all__ = ["AngelSystem", "get_angel_system"]
