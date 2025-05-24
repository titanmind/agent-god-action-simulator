
"""Basic LLM reasoning loop for AI-controlled agents."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from ...core.components.ai_state import AIState
from ...ai.llm.prompt_builder import build_prompt
from ...ai.llm.llm_manager import LLMManager
from .behavior_tree import BehaviorTree, build_fallback_tree


class AIReasoningSystem:
    """Query the LLM for each agent and queue resulting actions."""

    def __init__(
        self,
        world: Any,
        llm: LLMManager,
        action_tuples_list: List[Tuple[int, str]],
        behavior_tree: Optional[BehaviorTree] = None,
    ) -> None:
        self.world = world
        self.llm = llm
        self.action_tuples_list = action_tuples_list
        self.behavior_tree = behavior_tree or build_fallback_tree()

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
            
            if action_str == "<wait>" and self.behavior_tree:
                fallback = self.behavior_tree.run(entity_id, self.world)
                if fallback is not None:
                    action_str = fallback
            
            if action_str and action_str != "<wait>": # Only append if not empty and not <wait>
                self.action_tuples_list.append((entity_id, action_str))


__all__ = ["AIReasoningSystem"]