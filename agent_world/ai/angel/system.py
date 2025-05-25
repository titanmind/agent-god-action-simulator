"""Angel system for granting new abilities."""

from __future__ import annotations

from typing import Any
from pathlib import Path
import logging
import re

from . import generator as angel_generator
from . import templates
from .vault_index import get_vault_index
from ...core.components.known_abilities import KnownAbilitiesComponent
from ...core.components.ai_state import AIState
from ...persistence.event_log import append_event, ANGEL_ACTION
from ...utils.sandbox import run_in_sandbox


class AngelSystem:
    """Generate abilities via Vault lookup or LLM."""

    def __init__(self, world: Any) -> None:
        self.world = world
        self.request_queue: list[tuple[int, str]] = []

    # ------------------------------------------------------------------
    # Lifecycle stubs
    # ------------------------------------------------------------------
    def update(self, world: Any, tick: int) -> None:
        """Placeholder system update method."""
        return None

    def process_pending_requests(self) -> None:
        """Placeholder for processing queued Angel requests."""
        return None

    def queue_request(self, agent_id: int, description: str) -> dict:
        """Queue an ability generation request and process immediately for now."""
        self.request_queue.append((agent_id, description))
        return self.generate_and_grant(agent_id, description)

    def _grant_to_agent(self, agent_id: int, class_name: str) -> None:
        cm = getattr(self.world, "component_manager", None)
        if cm is None:
            return

        em = getattr(self.world, "entity_manager", None)
        if em is not None and not em.has_entity(agent_id):
            logging.warning(
                "AngelSystem: attempted to grant ability to unknown agent_id %s",
                agent_id,
            )
            return

        comp = cm.get_component(agent_id, KnownAbilitiesComponent)
        if comp is None:
            comp = KnownAbilitiesComponent()
            cm.add_component(agent_id, comp)
        if class_name not in comp.known_class_names:
            comp.known_class_names.append(class_name)
            ai_state = cm.get_component(agent_id, AIState)
            if ai_state is not None:
                ai_state.needs_immediate_rethink = True

    def generate_and_grant(self, agent_id: int, description: str) -> dict:
        """Generate an ability or fetch one from the vault."""
        if getattr(self.world, "component_manager", None) is None:
            # Stub path for early tests when world is not fully initialized
            return {"status": "stub"}
        dest = getattr(self.world, "persistent_event_log_path", None)
        if dest is None:
            dest = Path("persistent_events.log")
            setattr(self.world, "persistent_event_log_path", dest)
        tick = getattr(getattr(self.world, "time_manager", None), "tick_counter", 0)
        vault_match = get_vault_index().lookup(description)
        if vault_match:
            append_event(dest, tick, ANGEL_ACTION, {
                "stage": "vault_hit",
                "agent_id": agent_id,
                "description": description,
                "ability": vault_match,
            })
            self._grant_to_agent(agent_id, vault_match)
            append_event(dest, tick, ANGEL_ACTION, {
                "stage": "granted",
                "agent_id": agent_id,
                "ability": vault_match,
            })
            return {"status": "success", "ability_class_name": vault_match}

        llm = getattr(self.world, "llm_manager_instance", None)
        stub_code = None
        if llm is not None:
            prompt = self._build_angel_code_generation_prompt(
                description,
                templates.get_world_constraints_for_angel(),
                templates.get_code_scaffolds_for_angel(),
            )
            try:
                stub_code = llm.request(
                    prompt,
                    self.world,
                    model=getattr(llm, "angel_generation_model", None),
                )
            except TypeError:
                try:
                    stub_code = llm.request(prompt, self.world)
                except TypeError:
                    stub_code = llm.request(prompt)

        append_event(
            dest,
            tick,
            ANGEL_ACTION,
            {"stage": "llm_attempt", "agent_id": agent_id, "description": description},
        )

        try:
            if stub_code is None:
                path = angel_generator.generate_ability(description)
            else:
                path = angel_generator.generate_ability(description, stub_code=stub_code)
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
            append_event(dest, tick, ANGEL_ACTION, {
                "stage": "granted",
                "agent_id": agent_id,
                "ability": class_name,
            })
            return {"status": "success", "ability_class_name": class_name}
        except Exception as e:  # Ability generation failure
            cm = getattr(self.world, "component_manager", None)
            ai_state = None
            if cm is not None:
                ai_state = cm.get_component(agent_id, AIState)
            if ai_state is not None:
                ai_state.last_error = str(e)
                ai_state.needs_immediate_rethink = True
            append_event(dest, tick, ANGEL_ACTION, {
                "stage": "failure",
                "agent_id": agent_id,
                "description": description,
                "reason": str(e),
            })
            return {"status": "failure", "reason": str(e)}

    # ------------------------------------------------------------------
    # Prompt building stub
    # ------------------------------------------------------------------
    def _build_angel_code_generation_prompt(
        self,
        description: str,
        world_constraints: dict,
        code_scaffolds: dict,
    ) -> str:
        """Return an LLM prompt for generating ability code."""
        return ""

    # ------------------------------------------------------------------
    # Conceptual testing stub
    # ------------------------------------------------------------------
    def _conceptual_test_generated_code(
        self, generated_code: str, original_request: str
    ) -> bool:
        """Return True if generated code passes conceptual tests."""
        return True


def get_angel_system(world: Any) -> AngelSystem:
    """Return existing AngelSystem instance on world or create one."""
    if not hasattr(world, "angel_system_instance") or world.angel_system_instance is None:
        world.angel_system_instance = AngelSystem(world)
    return world.angel_system_instance


__all__ = ["AngelSystem", "get_angel_system"]
