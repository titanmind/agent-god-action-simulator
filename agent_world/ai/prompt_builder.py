"""Prompt building utilities with recent event injection."""

from __future__ import annotations

from typing import Optional

from .llm.prompt_builder import (
    build_prompt as _base_build_prompt,
    _normalize,
    _get_memories,
)
from ..core.world import World
from ..core.components.event_log import EventLog
from ..core.components.perception_cache import PerceptionCache
from ..core.components.ai_state import AIState


def build_prompt(agent_id: int, world: World, *, memory_k: int = 5) -> str:
    """Return an LLM prompt augmented with recent events for the agent."""

    prompt = _base_build_prompt(agent_id, world, memory_k=memory_k)

    cm = getattr(world, "component_manager", None)
    event_log: Optional[EventLog] = None
    ai_state: Optional[AIState] = None
    perception_cache: Optional[PerceptionCache] = None
    if cm is not None:
        perception_cache = cm.get_component(agent_id, PerceptionCache)
        event_log = cm.get_component(agent_id, EventLog)
        ai_state = cm.get_component(agent_id, AIState)

    events = []
    if perception_cache and perception_cache.visible_ability_uses:
        events = perception_cache.visible_ability_uses
    elif event_log and event_log.recent:
        events = list(event_log.recent)

    if events:
        event_lines = [f"- {ev.ability_name} by {ev.caster_id}" for ev in events]
        events_section = "Recent Events:\n" + "\n".join(event_lines)

        token = "--- FOCUS FOR THIS TURN ---"
        if token in prompt:
            prompt = prompt.replace(token, f"{events_section}\n\n{token}", 1)
        else:
            prompt = f"{prompt}\n\n{events_section}"

    if ai_state and ai_state.last_error:
        prompt = f"SYSTEM NOTE: {ai_state.last_error}\n\n{prompt}"

    return prompt


__all__ = ["build_prompt", "_normalize", "_get_memories"]
