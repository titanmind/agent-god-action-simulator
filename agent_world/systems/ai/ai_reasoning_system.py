
"""Basic LLM reasoning loop for AI-controlled agents."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

COOLDOWN_TICKS = 10

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
        """Handle pending and new LLM prompts for all agents."""

        if (
            self.world.entity_manager is None
            or self.world.component_manager is None
            or self.world.time_manager is None
        ):
            return

        em = self.world.entity_manager
        cm = self.world.component_manager
        tm = self.world.time_manager

        for entity_id in list(em.all_entities.keys()):
            state = cm.get_component(entity_id, AIState)
            if state is None:
                continue

            if tm.tick_counter <= state.last_llm_action_tick + COOLDOWN_TICKS:
                continue

            if state.pending_llm_prompt_id is None:
                prompt = build_prompt(entity_id, self.world)
                result = self.llm.request(prompt, self.world)

                if result and result in self.world.async_llm_responses:
                    state.pending_llm_prompt_id = result
                    continue

                action_str = result
                if action_str and action_str != "<wait>":
                    self.action_tuples_list.append((entity_id, action_str))
                    state.last_llm_action_tick = tm.tick_counter
                elif self.behavior_tree is not None:
                    fallback = self.behavior_tree.run(entity_id, self.world)
                    if fallback:
                        self.action_tuples_list.append((entity_id, fallback))
            else:
                fut = self.world.async_llm_responses.get(state.pending_llm_prompt_id)
                if fut is not None and fut.done():
                    action_str = (
                        self.world.async_llm_responses.pop(state.pending_llm_prompt_id).result()
                    )
                    if action_str and action_str != "<wait>":
                        self.action_tuples_list.append((entity_id, action_str))
                        state.last_llm_action_tick = tm.tick_counter
                    else:
                        if self.behavior_tree is not None:
                            fallback = self.behavior_tree.run(entity_id, self.world)
                            if fallback:
                                self.action_tuples_list.append((entity_id, fallback))
                    state.pending_llm_prompt_id = None


__all__ = ["AIReasoningSystem"]
