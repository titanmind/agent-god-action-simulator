# agent_world/systems/ai/ai_reasoning_system.py
"""Basic LLM reasoning loop for AI-controlled agents."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple
import re 
import logging

logger = logging.getLogger(__name__)

COOLDOWN_TICKS = 10 

from ...core.components.ai_state import AIState, ActionStep 
from ...ai.llm.prompt_builder import build_prompt
from ...ai.llm.llm_manager import LLMManager
from ...core.components.role import RoleComponent
from ...ai.planning.llm_planner import LLMPlanner
from ...core.components.position import Position
from ...systems.movement import pathfinding
from .behavior_tree import BehaviorTree, build_fallback_tree 
from .actions import parse_action_string, ActionQueue

NON_ACTION_STRINGS = [
    "<wait>", "<error_llm_call>", "<wait_llm_not_ready>", "<error_llm_setup>",
    "<error_llm_loop_missing>", "<error_llm_queue_full>", "<error_llm_no_choices>",
    "<error_llm_malformed_choice>", "<error_llm_malformed_message>",
    "<error_llm_malformed_content>", "<error_llm_request>", "<error_llm_parsing>",
    "<llm_empty_response>", "" 
]
for i in range(400, 600): NON_ACTION_STRINGS.append(f"<error_llm_http_{i}>")
PROMPT_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


class AIReasoningSystem:
    """Query the LLM for each agent and queue resulting actions."""

    def __init__(
        self,
        world: Any,
        llm: LLMManager,
        action_tuples_list: Any, 
        behavior_tree: Optional[BehaviorTree] = None, 
        planner: LLMPlanner | None = None,
    ) -> None:
        self.world = world
        self.llm = llm
        self.internal_fallback_bt = behavior_tree or build_fallback_tree()
        self.planner = planner or LLMPlanner(llm)
        self.action_queue: ActionQueue | None = getattr(world, "action_queue", None)

    @staticmethod
    def _first_obstacle_in_direct_path(start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[int, int] | None:
        x, y = start; gx, gy = goal
        while x != gx:
            x += 1 if gx > x else -1
            if pathfinding.is_blocked((x, y)): return (x, y)
        while y != gy:
            y += 1 if gy > y else -1
            if pathfinding.is_blocked((x, y)): return (x, y)
        return None

    def _contextualize_generate_ability(self, action_text: str, ai_comp: AIState, entity_id: int) -> str:
        if not action_text.upper().startswith("GENERATE_ABILITY"): return action_text
        parts = action_text.split(maxsplit=1)
        if len(parts) < 2: return action_text
        desc = parts[1]
        if re.search(r"\(\s*\d+\s*,\s*\d+\s*\)", desc): return action_text
        
        cm = self.world.component_manager
        obs_coords: Tuple[int, int] | None = None
        goal_target_display: Any = None

        agent_pos = cm.get_component(entity_id, Position)
        if ai_comp.goals and agent_pos:
            goal = ai_comp.goals[0]
            target_entity_id_or_coords = getattr(goal, "target", None)
            goal_target_display = target_entity_id_or_coords
            target_coords_tuple: Tuple[int, int] | None = None
            if isinstance(target_entity_id_or_coords, int):
                t_pos = cm.get_component(target_entity_id_or_coords, Position)
                if t_pos: target_coords_tuple = (t_pos.x, t_pos.y)
            elif isinstance(target_entity_id_or_coords, (tuple, list)) and len(target_entity_id_or_coords) == 2:
                try: target_coords_tuple = (int(target_entity_id_or_coords[0]), int(target_entity_id_or_coords[1]))
                except ValueError: pass
            if target_coords_tuple:
                obs_coords = self._first_obstacle_in_direct_path((agent_pos.x, agent_pos.y), target_coords_tuple)

        if obs_coords is not None:
            obs_str = f"({obs_coords[0]},{obs_coords[1]})"
            if obs_str not in desc:
                new_desc_parts = [desc]
                new_desc_parts.append(f"for obstacle at {obs_str}")
                if goal_target_display: new_desc_parts.append(f"blocking path to goal target {goal_target_display}")
                new_desc = " ".join(new_desc_parts)
                logger.info("[AIReasoningSystem] Contextualized GENERATE_ABILITY for agent %s: '%s' -> '%s'", entity_id, action_text, f"GENERATE_ABILITY {new_desc}")
                return f"GENERATE_ABILITY {new_desc}"
        return action_text

    def _convert_plan_step_to_action(self, step: ActionStep, entity_id: int) -> Optional[str]:
        action_verb_upper = step.action.upper()
        if action_verb_upper == "MOVE_TO":
            cm = self.world.component_manager; agent_pos = cm.get_component(entity_id, Position)
            if not agent_pos: return None
            target_coords = None
            if isinstance(step.target, int):
                target_pos = cm.get_component(step.target, Position)
                if target_pos: target_coords = (target_pos.x, target_pos.y)
            elif step.parameters.get("target_coords"): target_coords = step.parameters["target_coords"]
            elif isinstance(step.target, (tuple, list)) and len(step.target) == 2:
                target_coords = (int(step.target[0]), int(step.target[1]))
            if target_coords:
                dx = target_coords[0] - agent_pos.x; dy = target_coords[1] - agent_pos.y
                if agent_pos.x == target_coords[0] and agent_pos.y == target_coords[1]:
                    return "IDLE" # Already at target, effectively an IDLE from this step
                if abs(dx) > abs(dy): return "MOVE E" if dx > 0 else "MOVE W"
                elif dy != 0: return "MOVE S" if dy > 0 else "MOVE N"
                else: return "IDLE" # Should be covered by at target check
        elif action_verb_upper in {"MOVE", "IDLE", "PICKUP", "ATTACK"}:
            action_parts = [action_verb_upper]
            if step.target is not None: action_parts.append(str(step.target))
            elif step.parameters.get("arg"): action_parts.append(str(step.parameters["arg"]))
            return " ".join(action_parts)
        elif action_verb_upper == "USE_ABILITY":
            ability_name = step.parameters.get("ability_name", step.parameters.get("arg")) 
            if not ability_name and " " in step.action: 
                ability_name = step.action.split(maxsplit=1)[1]
            if ability_name:
                action_parts = [action_verb_upper, str(ability_name)]
                target_val = step.target if step.target is not None else step.parameters.get("target_id")
                if target_val is not None: action_parts.append(str(target_val))
                return " ".join(action_parts)
        return None

    def update(self, tick: int) -> None:
        if not all([self.world.entity_manager, self.world.component_manager, self.world.time_manager,
                    self.world.llm_manager_instance, hasattr(self.world, 'async_llm_responses')]):
            return
        if self.action_queue is None: self.action_queue = getattr(self.world, "action_queue", None)
        if self.action_queue is None: logger.critical("[AIReasoningSystem] CRITICAL: ActionQueue not found."); return

        em = self.world.entity_manager; cm = self.world.component_manager; tm = self.world.time_manager
        
        for entity_id in list(em.all_entities.keys()):
            ai_comp = cm.get_component(entity_id, AIState)
            if ai_comp is None: continue

            role_comp = cm.get_component(entity_id, RoleComponent)
            if role_comp and not role_comp.uses_llm: continue 

            final_action_to_take: str | None = None
            
            # Task 5.2: Agent is waiting for an ability to be generated.
            if ai_comp.waiting_for_ability_generation_desc is not None:
                logger.debug("[Tick %s][AI Agent %s] Waiting for ability generation ('%s'). Skipping other reasoning.", tm.tick_counter, entity_id, ai_comp.waiting_for_ability_generation_desc)
                continue # Agent does nothing else this tick

            previous_action_failed = ai_comp.last_action_failed_to_achieve_effect
            ai_comp.last_action_failed_to_achieve_effect = False 

            current_plan_step: ActionStep | None = ai_comp.current_plan[0] if ai_comp.current_plan else None
            
            if previous_action_failed and current_plan_step:
                logger.debug("[Tick %s][AI Agent %s] Previous action for plan step '%s' failed. Incrementing step retries from %s.", tm.tick_counter, entity_id, current_plan_step.action, current_plan_step.retries)
                current_plan_step.retries += 1
            
            if current_plan_step and current_plan_step.retries > ai_comp.max_plan_step_retries:
                logger.warning("[Tick %s][AI Agent %s] Max retries (%s) exceeded for plan step: %s. Clearing plan.", tm.tick_counter, entity_id, ai_comp.max_plan_step_retries, current_plan_step)
                ai_comp.current_plan.clear(); current_plan_step = None
                ai_comp.pending_llm_prompt_id = None; ai_comp.pending_llm_for_plan_step_action = None
                ai_comp.last_plan_generation_tick = tm.tick_counter 
            
            # Task 5.2: If newly_generated_ability_name is set, try to use it.
            if ai_comp.newly_generated_ability_name:
                ability_to_use = ai_comp.newly_generated_ability_name
                ai_comp.newly_generated_ability_name = None # Consume the hint
                # Attempt to find a relevant target (e.g., obstacle from original problem)
                # This part is heuristic. A more robust way would be for AngelSystem to store context.
                target_id_for_new_ability: Optional[int] = None
                obstacle_coords_str_from_desc = None
                if ai_comp.last_error and "obstacle at" in ai_comp.last_error: # if previous error mentioned obstacle
                    match = re.search(r"obstacle at \((\d+,\s*\d+)\)", ai_comp.last_error)
                    if match: obstacle_coords_str_from_desc = match.group(1)
                
                # For now, let LLM decide target in the rethink if USE_ABILITY needs one.
                # Or, if the ability is general (no target), it will just be used.
                final_action_to_take = f"USE_ABILITY {ability_to_use}"
                # If we could determine a target (e.g. from a parsed obstacle_coords_str_from_desc),
                # we would append it here. For simplicity, let the next LLM call handle target if USE_ABILITY fails without one.
                logger.info("[Tick %s][AI Agent %s] Attempting to use newly generated ability: '%s'", tm.tick_counter, entity_id, final_action_to_take)
                # This action will be enqueued. The plan (if any) remains.
                # The 'needs_immediate_rethink' will still be true, prompting a fresh look next cycle.

            if final_action_to_take is None and (ai_comp.goals and not ai_comp.current_plan and
                ai_comp.last_plan_generation_tick != tm.tick_counter and
                ai_comp.pending_llm_prompt_id is None):
                logger.debug("[Tick %s][AI Agent %s] Has goals, no plan. Requesting new plan.", tm.tick_counter, entity_id)
                ai_comp.current_plan = self.planner.create_plan(entity_id, ai_comp.goals, self.world)
                ai_comp.last_plan_generation_tick = tm.tick_counter
                if ai_comp.current_plan:
                    logger.info("[Tick %s][AI Agent %s] Planner generated new plan: %s", tm.tick_counter, entity_id, [str(s) for s in ai_comp.current_plan])
                    current_plan_step = ai_comp.current_plan[0] # Update current_plan_step after new plan
                else: logger.warning("[Tick %s][AI Agent %s] Planner failed to generate a plan.", tm.tick_counter, entity_id)

            bypass_cooldown = False
            if ai_comp.needs_immediate_rethink:
                logger.debug("[Tick %s][AI Agent %s] Needs immediate rethink.", tm.tick_counter, entity_id)
                ai_comp.needs_immediate_rethink = False; bypass_cooldown = True
            
            if (not final_action_to_take and not bypass_cooldown and 
                tm.tick_counter <= ai_comp.last_llm_action_tick + COOLDOWN_TICKS and
                ai_comp.last_llm_action_tick != -1):
                continue

            if final_action_to_take is None and current_plan_step:
                step_action_key = f"{current_plan_step.action}_{id(current_plan_step)}"
                direct_action = self._convert_plan_step_to_action(current_plan_step, entity_id)

                if direct_action:
                    final_action_to_take = direct_action
                    logger.info("[Tick %s][AI Agent %s] Directly executing plan step: '%s' -> '%s'", tm.tick_counter, entity_id, current_plan_step.action, final_action_to_take)
                    ai_comp.current_plan.pop(0)
                    current_plan_step.retries = 0 # Reset retries for this step as it's popped
                    ai_comp.general_action_retries = 0 
                else: 
                    if ai_comp.pending_llm_prompt_id is None or ai_comp.pending_llm_for_plan_step_action != step_action_key:
                        prompt_context = f"\nSYSTEM TASK: Current plan step: {current_plan_step.action}"
                        if current_plan_step.step_type == "deal_with_obstacle":
                            coords = current_plan_step.parameters.get("coords_str") or current_plan_step.parameters.get("coords") or current_plan_step.parameters.get("obstacle_ref")
                            prompt_context = f"\nSYSTEM TASK: Obstacle at {coords} blocks your path. Plan action to deal with it."
                        elif current_plan_step.step_type == "generate_ability": # From planner
                            desc = current_plan_step.parameters.get("description", "solve a problem")
                            prompt_context = f"\nSYSTEM TASK: You need to generate an ability for: '{desc}'. Formulate the GENERATE_ABILITY action string."
                        
                        prompt = build_prompt(entity_id, self.world) + prompt_context
                        if role_comp and not role_comp.can_request_abilities:
                            prompt = "\n".join(l for l in prompt.splitlines() if "GENERATE_ABILITY" not in l.upper())
                        
                        returned_value = self.llm.request(prompt, self.world)
                        if PROMPT_ID_PATTERN.match(returned_value):
                            ai_comp.pending_llm_prompt_id = returned_value
                            ai_comp.pending_llm_for_plan_step_action = step_action_key
                            logger.debug("[Tick %s][AI Agent %s] LLM request for plan step '%s'. Prompt ID: %s.", tm.tick_counter, entity_id, current_plan_step.action, returned_value)
                        elif returned_value not in NON_ACTION_STRINGS:
                            final_action_to_take = returned_value
                            logger.info("[Tick %s][AI Agent %s] LLM immediate action for plan step '%s': '%s'", tm.tick_counter, entity_id, current_plan_step.action, final_action_to_take.replace('\n','//'))
                            ai_comp.current_plan.pop(0)
                            current_plan_step.retries = 0 
                            ai_comp.general_action_retries = 0
                        else: 
                            logger.warning("[Tick %s][AI Agent %s] LLM immediate non-action '%s' for plan step '%s'. Incrementing step retries.", tm.tick_counter, entity_id, returned_value, current_plan_step.action)
                            current_plan_step.retries += 1
                            ai_comp.last_llm_action_tick = tm.tick_counter # Cooldown on failed LLM for step
                    
                    elif ai_comp.pending_llm_prompt_id is not None and ai_comp.pending_llm_for_plan_step_action == step_action_key:
                        future = self.world.async_llm_responses.get(ai_comp.pending_llm_prompt_id)
                        if future and future.done():
                            try: action_from_llm = future.result()
                            except Exception as e: action_from_llm = f"<error_llm_future_exception: {e}>"
                            
                            logger.debug("[Tick %s][AI Agent %s] LLM Future for plan step '%s' resolved. Result: '%s'", tm.tick_counter, entity_id, current_plan_step.action, action_from_llm.replace('\n','//'))
                            self.world.async_llm_responses.pop(ai_comp.pending_llm_prompt_id, None)
                            ai_comp.pending_llm_prompt_id = None
                            ai_comp.pending_llm_for_plan_step_action = None

                            if action_from_llm not in NON_ACTION_STRINGS:
                                final_action_to_take = action_from_llm
                                ai_comp.current_plan.pop(0)
                                current_plan_step.retries = 0 
                                ai_comp.general_action_retries = 0
                            else: 
                                logger.warning("[Tick %s][AI Agent %s] LLM future non-action '%s' for plan step '%s'. Incrementing step retries.", tm.tick_counter, entity_id, action_from_llm, current_plan_step.action)
                                current_plan_step.retries += 1
                                ai_comp.last_llm_action_tick = tm.tick_counter # Cooldown

            if final_action_to_take is None and ai_comp.pending_llm_prompt_id is None and not current_plan_step:
                prompt = build_prompt(entity_id, self.world)
                if role_comp and not role_comp.can_request_abilities:
                    prompt = "\n".join(l for l in prompt.splitlines() if "GENERATE_ABILITY" not in l.upper())
                returned_value = self.llm.request(prompt, self.world)
                if PROMPT_ID_PATTERN.match(returned_value):
                    ai_comp.pending_llm_prompt_id = returned_value
                    logger.debug("[Tick %s][AI Agent %s] General LLM request (no plan). Prompt ID: %s.", tm.tick_counter, entity_id, returned_value)
                elif returned_value not in NON_ACTION_STRINGS:
                    final_action_to_take = returned_value
                    logger.info("[Tick %s][AI Agent %s] General LLM immediate action (no plan): '%s'", tm.tick_counter, entity_id, final_action_to_take.replace('\n','//'))
                    ai_comp.general_action_retries = 0
                else: 
                    logger.debug("[Tick %s][AI Agent %s] General LLM immediate non-action (no plan): '%s'. Retries: %s", tm.tick_counter, entity_id, returned_value, ai_comp.general_action_retries)
                    ai_comp.general_action_retries +=1
                    ai_comp.last_llm_action_tick = tm.tick_counter 
                    if ai_comp.general_action_retries > ai_comp.max_plan_step_retries: 
                        logger.warning("[Tick %s][AI Agent %s] Max general action retries. Will fallback to BT if available.", tm.tick_counter, entity_id)
            
            if final_action_to_take is None and ai_comp.pending_llm_prompt_id is None:
                if self.internal_fallback_bt:
                    logger.debug("[Tick %s][AI Agent %s] No LLM action decided and not waiting. Using internal BT fallback.", tm.tick_counter, entity_id)
                    fallback_action = self.internal_fallback_bt.run(entity_id, self.world)
                    if fallback_action:
                        final_action_to_take = fallback_action
                        logger.info("[Tick %s][AI Agent %s] Internal BT fallback action: '%s'", tm.tick_counter, entity_id, fallback_action)
            
            if final_action_to_take:
                if final_action_to_take.upper().startswith("GENERATE_ABILITY"):
                    final_action_to_take = self._contextualize_generate_ability(final_action_to_take, ai_comp, entity_id)
                
                logger.info("[Tick %s][AI Agent %s] Final Enqueued Action: '%s'", tm.tick_counter, entity_id, final_action_to_take.replace("\n", "//"))
                parsed_actions_list = parse_action_string(entity_id, final_action_to_take)
                for act_obj in parsed_actions_list:
                    self.action_queue._queue.append(act_obj)
                ai_comp.last_llm_action_tick = tm.tick_counter
            
            elif ai_comp.pending_llm_prompt_id is None: 
                logger.debug("[Tick %s][AI Agent %s] No action decided, not waiting for LLM. Effective idle. Cooldown applies.", tm.tick_counter, entity_id)
                ai_comp.last_llm_action_tick = tm.tick_counter

class RawActionCollector(list[tuple[int, str]]):
    def __init__(self, action_queue: ActionQueue) -> None:
        super().__init__()
        self.action_queue = action_queue
    def append(self, item: tuple[int, str]) -> None:
        actor_id, text = item
        if self.action_queue is not None:
            parsed = parse_action_string(actor_id, text)
            for act in parsed: self.action_queue._queue.append(act)
        super().append(item)

__all__ = ["AIReasoningSystem", "RawActionCollector"]