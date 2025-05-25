"""Stub helpers for Angel prompt templates."""

from __future__ import annotations


def get_world_constraints_for_angel() -> dict:
    """Return world constraint information for Angel LLM.

    The Angel LLM only needs a small subset of the world structure.  This helper
    introspects the :class:`World` container and the :class:`Ability` base class
    to expose high level API information.  The return value is a plain
    dictionary so it can be JSON serialised directly inside LLM prompts.
    """

    from agent_world.core.world import World
    from agent_world.abilities.base import Ability

    dummy_world = World((1, 1))

    world_attrs = [
        name
        for name in vars(dummy_world).keys()
        if name
        in {
            "entity_manager",
            "component_manager",
            "systems_manager",
            "time_manager",
            "action_queue",
            "llm_manager_instance",
        }
    ]

    ability_methods = [m for m in dir(Ability) if not m.startswith("_")]

    return {
        "world_attributes": sorted(world_attrs),
        "ability_base_methods": sorted(ability_methods),
        "max_code_lines": 100,
    }


def get_code_scaffolds_for_angel() -> dict:
    """Return code scaffold snippets for Angel LLM.

    The returned dictionary provides minimal Python templates that the Angel
    language model can use as a starting point when generating new abilities.
    It intentionally mirrors the structure expected by ``generator.generate_ability``.
    """

    imports = (
        "from agent_world.abilities.base import Ability\n"
        "from typing import Any, Optional"
    )

    class_template = (
        "class {class_name}(Ability):\n"
        "    \"\"\"Auto-generated ability\"\"\"\n"
        "    @property\n"
        "    def energy_cost(self) -> int: return 0\n\n"
        "    @property\n"
        "    def cooldown(self) -> int: return 1\n\n"
        "    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:\n"
        "        return True\n\n"
        "    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:\n"
        "        pass"
    )

    return {"imports": imports, "ability_class_template": class_template}


__all__ = [
    "get_world_constraints_for_angel",
    "get_code_scaffolds_for_angel",
]

