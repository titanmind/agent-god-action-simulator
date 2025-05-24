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


def build_prompt(agent_id: int, world: World, *, memory_k: int = 5) -> str:
    """Return an LLM prompt augmented with recent events for the agent."""

    prompt = _base_build_prompt(agent_id, world, memory_k=memory_k)

    cm = getattr(world, "component_manager", None)
    event_log: Optional[EventLog] = None
    if cm is not None:
        event_log = cm.get_component(agent_id, EventLog)

    if event_log and event_log.recent:
        event_lines = [f"- {ev.ability_name} by {ev.caster_id}" for ev in event_log.recent]
        events_section = "Recent Events:\n" + "\n".join(event_lines)

        token = "--- FOCUS FOR THIS TURN ---"
        if token in prompt:
            prompt = prompt.replace(token, f"{events_section}\n\n{token}", 1)
        else:
            prompt = f"{prompt}\n\n{events_section}"

    return prompt


__all__ = ["build_prompt", "_normalize", "_get_memories"]
