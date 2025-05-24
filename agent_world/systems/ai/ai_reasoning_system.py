"""Basic LLM reasoning loop for AI-controlled agents."""

from __future__ import annotations

from typing import Any, List

from ...core.components.ai_state import AIState
from ...ai.llm.prompt_builder import build_prompt
from ...ai.llm.llm_manager import LLMManager


class AIReasoningSystem:
    """Query the LLM for each agent and queue resulting actions."""

    def __init__(self, world: Any, llm: LLMManager, action_queue: List[str]) -> None:
        self.world = world
        self.llm = llm
        self.action_queue = action_queue

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, tick: int) -> None:
        """Build prompts for agents and enqueue LLM completions."""

        if self.world.entity_manager is None or self.world.component_manager is None:
            return

        em = self.world.entity_manager
        cm = self.world.component_manager

        for entity_id in list(em.all_entities.keys()):
            state = cm.get_component(entity_id, AIState)
            if state is None:
                continue

            prompt = build_prompt(entity_id, self.world)
            action_str = self.llm.request(prompt, timeout=0.05)
            self.action_queue.append(action_str)


__all__ = ["AIReasoningSystem"]
