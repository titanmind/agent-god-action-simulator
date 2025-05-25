
# agent_world/systems/ai/ai_reasoning_system.py
"""Basic LLM reasoning loop for AI-controlled agents."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Dict
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
from .actions import parse_action_string, ActionQueue, GenerateAbilityAction 

NON_ACTION_STRINGS = [
    "<wait>", "<error_llm_call>", "<wait_llm_not_ready>", "<error_llm_setup>",
    "<error_llm_loop_missing>", "<error_llm_queue_full>", "<error_llm_no_choices>",
    "<error_llm_malformed_choice>", "<error_llm_malformed_message>",
    "<error_llm_malformed_content>", "<error_llm_request>", "<error_llm_parsing>",
    "<llm_empty_response>", "<error_llm_future_not_found>", "<error_llm_timeout>",
    "<error_llm_future_exception>" 
]
for i in range(400, 600): NON_ACTION_STRINGS.append(f"<error_llm_http_{i}>")
NON_ACTION_STRINGS.extend([s + "_None" for s in NON_ACTION_STRINGS if s.endswith(">")]) 
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

    def _contextualize_generate_ability(self, action_text: str, ai_comp: AIState, entity_id: int) -> Tuple[str, Optional[Dict[str, Any]]]:
        step_context_for_angel: Optional[Dict[str, Any]] = None
        if not action_text.upper().startswith("GENERATE_ABILITY"): return action_text, step_context_for_angel
        
        parts = action_text.split(maxsplit=1)
        if len(parts) < 2: return action_text, step_context_for_angel
        desc = parts[1]
        
        if ai_comp.current_plan: 
            current_step = ai_comp.current_plan[0]
            step_context_for_angel = {
                "original_step_action": current_step.action,
                "original_step_parameters": current_step.parameters.copy() if current_step.parameters else {},
                "original_step_type": current_step.step_type,
                "original_step_target": current_step.target
            }
            if (current_step.step_type == "deal_with_obstacle" or 
                (current_step.action and current_step.action.upper() == "DEAL_WITH_OBSTACLE")):
                coords = current_step.parameters.get("coords_str") or current_step.parameters.get("coords") or current_step.parameters.get("obstacle_ref")
                if coords: step_context_for_angel["obstacle_coords"] = coords

        if re.search(r"\(\s*\d+\s*,\s*\d+\s*\)", desc): return action_text, step_context_for_angel 
        
        cm = self.world.component_manager
        obs_coords: Tuple[int, int] | None = None
        goal_target_display: Any = None

        if step_context_for_angel and step_context_for_angel.get("obstacle_coords"):
            raw_coords = step_context_for_angel["obstacle_coords"]
            if isinstance(raw_coords, tuple) and len(raw_coords) == 2: obs_coords = raw_coords
            elif isinstance(raw_coords, str) and "," in raw_coords:
                try:
                    x_str, y_str = raw_coords.strip("()").split(',')
                    obs_coords = (int(x_str.strip()), int(y_str.strip()))
                except: pass

        if obs_coords is None: 
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
            if step_context_for_angel: 
                if "obstacle_coords" not in step_context_for_angel : step_context_for_angel["obstacle_coords"] = obs_coords
            else: 
                step_context_for_angel = {"obstacle_coords": obs_coords}
            if obs_str not in desc:
                new_desc_parts = [desc, f"for obstacle at {obs_str}"]
                if goal_target_display: new_desc_parts.append(f"blocking path to goal target {goal_target_display}")
                new_desc = " ".join(new_desc_parts)
                logger.info("[AIReasoningSystem] Contextualized GENERATE_ABILITY for agent %s: '%s' -> '%s'", entity_id, action_text, f"GENERATE_ABILITY {new_desc}")
                return f"GENERATE_ABILITY {new_desc}", step_context_for_angel
        return action_text, step_context_for_angel

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
                if agent_pos.x == target_coords[0] and agent_pos.y == target_coords[1]:
                    return "IDLE" 
                dx = target_coords[0] - agent_pos.x; dy = target_coords[1] - agent_pos.y
                if abs(dx) > abs(dy): return "MOVE E" if dx > 0 else "MOVE W"
                elif dy != 0: return "MOVE S" if dy > 0 else "MOVE N"
                else: return "IDLE" 
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
            angel_step_context: Optional[Dict[str,Any]] = None
            
            if ai_comp.waiting_for_ability_generation_desc is not None:
                logger.debug("[Tick %s][AI Agent %s] Waiting for ability generation ('%s').", tm.tick_counter, entity_id, ai_comp.waiting_for_ability_generation_desc)
                continue 

            previous_action_failed = ai_comp.last_action_failed_to_achieve_effect
            ai_comp.last_action_failed_to_achieve_effect = False 

            current_plan_step: ActionStep | None = ai_comp.current_plan[0] if ai_comp.current_plan else None
            
            # Task 10.1: Handle last_error (e.g. from Angel failure) for current plan step
            if ai_comp.last_error and current_plan_step:
                is_relevant_error = False
                # Check if the context of the error matches the current step
                # This relies on newly_generated_ability_context being set *before* Angel call
                # and *not cleared* if Angel fails for that context.
                ctx = ai_comp.newly_generated_ability_context
                if ctx and ctx.get("original_step_action") == current_plan_step.action and \
                   ctx.get("original_step_parameters") == current_plan_step.parameters and \
                   ctx.get("original_step_type") == current_plan_step.step_type and \
                   ctx.get("original_step_target") == current_plan_step.target:
                    is_relevant_error = True
                
                if is_relevant_error:
                    logger.warning("[Tick %s][AI Agent %s] Last AngelSystem error ('%s') IS relevant to plan step '%s'. Incrementing step retries.", tm.tick_counter, entity_id, ai_comp.last_error, current_plan_step.action)
                    current_plan_step.retries += 1
                else:
                    logger.debug("[Tick %s][AI Agent %s] Last AngelSystem error ('%s') NOT deemed relevant to current step '%s' based on context. Context: %s", tm.tick_counter, entity_id, ai_comp.last_error, current_plan_step.action if current_plan_step else "None", ctx)
                # The error will be included in the prompt by prompt_builder, so it's "processed" for that.
                # AIReasoningSystem doesn't need to clear it here, prompt_builder or next successful Angel call will.
            
            # Check for plan step completion first (e.g. obstacle gone)
            if current_plan_step and (current_plan_step.step_type == "deal_with_obstacle" or \
                                      (current_plan_step.action and current_plan_step.action.upper() == "DEAL_WITH_OBSTACLE")):
                coords_param = current_plan_step.parameters.get("coords")
                obstacle_coords_to_check = None
                if isinstance(coords_param, (list,tuple)) and len(coords_param) == 2:
                    try: obstacle_coords_to_check = (int(coords_param[0]), int(coords_param[1]))
                    except ValueError: pass
                elif isinstance(coords_param, str) and "," in coords_param: # Handle string like "(x,y)"
                     try:
                        x_str, y_str = coords_param.strip("()").split(',')
                        obstacle_coords_to_check = (int(x_str.strip()), int(y_str.strip()))
                     except ValueError: pass

                if obstacle_coords_to_check and not pathfinding.is_blocked(obstacle_coords_to_check):
                    logger.info("[Tick %s][AI Agent %s] Obstacle at %s for step '%s' is GONE. Popping step.", tm.tick_counter, entity_id, obstacle_coords_to_check, current_plan_step.action)
                    ai_comp.current_plan.pop(0)
                    current_plan_step.retries = 0 
                    current_plan_step = ai_comp.current_plan[0] if ai_comp.current_plan else None 
                    ai_comp.general_action_retries = 0 

            if previous_action_failed and current_plan_step: 
                logger.debug("[Tick %s][AI Agent %s] Previous action for plan step '%s' failed. Incrementing step retries from %s.", tm.tick_counter, entity_id, current_plan_step.action, current_plan_step.retries)
                current_plan_step.retries += 1
            
            if current_plan_step and current_plan_step.retries > ai_comp.max_plan_step_retries:
                logger.warning("[Tick %s][AI Agent %s] Max retries (%s) exceeded for plan step: %s. Clearing plan.", tm.tick_counter, entity_id, ai_comp.max_plan_step_retries, current_plan_step)
                ai_comp.current_plan.clear(); current_plan_step = None
                ai_comp.pending_llm_prompt_id = None; ai_comp.pending_llm_for_plan_step_action = None
                ai_comp.last_plan_generation_tick = tm.tick_counter 
            
            if ai_comp.newly_generated_ability_name and current_plan_step: 
                new_ability = ai_comp.newly_generated_ability_name
                context_for_new_ability = ai_comp.newly_generated_ability_context
                ai_comp.newly_generated_ability_name = None 
                # Keep newly_generated_ability_context until the USE_ABILITY action related to it is taken or fails

                final_action_to_take = f"USE_ABILITY {new_ability}"
                logger.info("[Tick %s][AI Agent %s] Attempting to use newly generated ability '%s' for current plan step '%s'. Context: %s", tm.tick_counter, entity_id, new_ability, current_plan_step.action, context_for_new_ability)

            if final_action_to_take is None and (ai_comp.goals and not ai_comp.current_plan and
                ai_comp.last_plan_generation_tick != tm.tick_counter and
                ai_comp.pending_llm_prompt_id is None):
                logger.debug("[Tick %s][AI Agent %s] Has goals, no plan. Requesting new plan.", tm.tick_counter, entity_id)
                ai_comp.current_plan = self.planner.create_plan(entity_id, ai_comp.goals, self.world)
                ai_comp.last_plan_generation_tick = tm.tick_counter
                if ai_comp.current_plan:
                    logger.info("[Tick %s][AI Agent %s] Planner generated new plan: %s", tm.tick_counter, entity_id, [str(s) for s in ai_comp.current_plan])
                    current_plan_step = ai_comp.current_plan[0] if ai_comp.current_plan else None
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
                    if direct_action == "IDLE" and current_plan_step.action.upper() == "MOVE_TO":
                        logger.info("[Tick %s][AI Agent %s] Plan step '%s' resulted in IDLE (target reached). Popping step.", tm.tick_counter, entity_id, current_plan_step.action)
                        ai_comp.current_plan.pop(0)
                        ai_comp.general_action_retries = 0
                        final_action_to_take = None 
                    else:
                        final_action_to_take = direct_action
                        logger.info("[Tick %s][AI Agent %s] Directly executing plan step: '%s' -> '%s'", tm.tick_counter, entity_id, current_plan_step.action, final_action_to_take)
                        ai_comp.current_plan.pop(0) 
                        ai_comp.general_action_retries = 0
                else: 
                    if ai_comp.pending_llm_prompt_id is None or ai_comp.pending_llm_for_plan_step_action != step_action_key:
                        prompt_context = f"\nSYSTEM TASK: Current plan step: {current_plan_step.action}"
                        if current_plan_step.step_type == "deal_with_obstacle":
                            coords = current_plan_step.parameters.get("coords_str") or current_plan_step.parameters.get("coords") or current_plan_step.parameters.get("obstacle_ref")
                            prompt_context = f"\nSYSTEM TASK: Obstacle at {coords} blocks your path. Plan action to deal with it."
                            if current_plan_step.retries > 0: # Task 11.1
                                prompt_context += (
                                    f"\nPrevious attempts to resolve this (retries: {current_plan_step.retries}) have not succeeded. "
                                    f"Last error for this was: {ai_comp.last_error or 'None'}.\n"
                                    "Consider a DIFFERENT action (e.g. USE_ABILITY, another GENERATE_ABILITY with different description, or MOVE if applicable) or a significantly different ability description."
                                )
                        elif current_plan_step.step_type == "generate_ability": 
                            desc = current_plan_step.parameters.get("description", "solve a problem")
                            prompt_context = f"\nSYSTEM TASK: You need to generate an ability for: '{desc}'. Formulate the GENERATE_ABILITY action string."
                        
                        prompt = build_prompt(entity_id, self.world) + prompt_context
                        if role_comp and not role_comp.can_request_abilities:
                            prompt = "\n".join(l for l in prompt.splitlines() if "GENERATE_ABILITY" not in l.upper())
                        
                        # Clear last_error if it's for the *same* step we are now prompting for
                        if ai_comp.last_error and ai_comp.newly_generated_ability_context and \
                           ai_comp.newly_generated_ability_context.get("original_step_action") == current_plan_step.action:
                            logger.debug("[Tick %s][AI Agent %s] Clearing last_error as we re-prompt for the same failed step.", tm.tick_counter, entity_id)
                            ai_comp.last_error = None 
                            # Keep newly_generated_ability_context until a new GENERATE_ABILITY for this step is chosen
                            # or the step is resolved/abandoned.
                            
                        returned_value = self.llm.request(prompt, self.world)
                        if PROMPT_ID_PATTERN.match(returned_value):
                            ai_comp.pending_llm_prompt_id = returned_value
                            ai_comp.pending_llm_for_plan_step_action = step_action_key
                            logger.debug("[Tick %s][AI Agent %s] LLM request for plan step '%s'. Prompt ID: %s.", tm.tick_counter, entity_id, current_plan_step.action, returned_value)
                        elif returned_value not in NON_ACTION_STRINGS:
                            final_action_to_take = returned_value
                            logger.info("[Tick %s][AI Agent %s] LLM immediate action for plan step '%s': '%s'", tm.tick_counter, entity_id, current_plan_step.action, final_action_to_take.replace('\n','//'))
                            # Task 9.1: Do NOT pop DEAL_WITH_OBSTACLE or steps that result in GENERATE_ABILITY.
                            if not final_action_to_take.upper().startswith("GENERATE_ABILITY") and \
                               not (current_plan_step.step_type == "deal_with_obstacle" or \
                                   (current_plan_step.action and current_plan_step.action.upper() == "DEAL_WITH_OBSTACLE")):
                                ai_comp.current_plan.pop(0)
                            # current_plan_step.retries = 0 # Reset on any valid action from LLM for this step
                            ai_comp.general_action_retries = 0
                        else: 
                            logger.warning("[Tick %s][AI Agent %s] LLM immediate non-action '%s' for plan step '%s'. Incrementing step retries.", tm.tick_counter, entity_id, returned_value, current_plan_step.action)
                            current_plan_step.retries += 1
                            ai_comp.last_llm_action_tick = tm.tick_counter 
                    
                    elif ai_comp.pending_llm_prompt_id is not None and ai_comp.pending_llm_for_plan_step_action == step_action_key:
                        future = self.world.async_llm_responses.get(ai_comp.pending_llm_prompt_id)
                        if future and future.done():
                            try: action_from_llm = future.result()
                            except Exception as e: action_from_llm = f"<error_llm_future_exception_{type(e).__name__}>"
                            
                            logger.debug("[Tick %s][AI Agent %s] LLM Future for plan step '%s' resolved. Result: '%s'", tm.tick_counter, entity_id, current_plan_step.action, action_from_llm.replace('\n','//'))
                            self.world.async_llm_responses.pop(ai_comp.pending_llm_prompt_id, None)
                            ai_comp.pending_llm_prompt_id = None
                            ai_comp.pending_llm_for_plan_step_action = None

                            if action_from_llm not in NON_ACTION_STRINGS:
                                final_action_to_take = action_from_llm
                                if not final_action_to_take.upper().startswith("GENERATE_ABILITY") and \
                                   not (current_plan_step.step_type == "deal_with_obstacle" or \
                                       (current_plan_step.action and current_plan_step.action.upper() == "DEAL_WITH_OBSTACLE")):
                                     ai_comp.current_plan.pop(0)
                                # current_plan_step.retries = 0 
                                ai_comp.general_action_retries = 0
                            else: 
                                logger.warning("[Tick %s][AI Agent %s] LLM future non-action '%s' for plan step '%s'. Incrementing step retries.", tm.tick_counter, entity_id, action_from_llm, current_plan_step.action)
                                current_plan_step.retries += 1
                                ai_comp.last_llm_action_tick = tm.tick_counter 
            
            if final_action_to_take is None and ai_comp.pending_llm_prompt_id is None and not current_plan_step:
                prompt = build_prompt(entity_id, self.world)
                if role_comp and not role_comp.can_request_abilities:
                    prompt = "\n".join(l for l in prompt.splitlines() if "GENERATE_ABILITY" not in l.upper())
                if ai_comp.last_error: # Clear general error if we're making a general LLM call
                    ai_comp.last_error = None

                returned_value = self.llm.request(prompt, self.world)
                if PROMPT_ID_PATTERN.match(returned_value):
                    ai_comp.pending_llm_prompt_id = returned_value 
                    logger.debug("[Tick %s][AI Agent %s] General LLM request (no plan). Prompt ID: %s.", tm.tick_counter, entity_id, returned_value)
                elif returned_value not in NON_ACTION_STRINGS:
                    final_action_to_take = returned_value
                    logger.info("[Tick %s][AI Agent %s] General LLM immediate action (no plan): '%s'", tm.tick_counter, entity_id, final_action_to_take.replace('\n','//'))
                    ai_comp.general_action_retries = 0
                else: 
                    logger.debug("[Tick %s][AI Agent %s] General LLM non-action (no plan): '%s'. Retries: %s", tm.tick_counter, entity_id, returned_value, ai_comp.general_action_retries)
                    ai_comp.general_action_retries +=1
                    ai_comp.last_llm_action_tick = tm.tick_counter 
                    if ai_comp.general_action_retries > ai_comp.max_plan_step_retries: 
                        logger.warning("[Tick %s][AI Agent %s] Max general action retries. Will fallback to BT.", tm.tick_counter, entity_id)
            
            if final_action_to_take is None and ai_comp.pending_llm_prompt_id is None:
                if self.internal_fallback_bt:
                    logger.debug("[Tick %s][AI Agent %s] No LLM action, not waiting. Using internal BT fallback.", tm.tick_counter, entity_id)
                    fallback_action = self.internal_fallback_bt.run(entity_id, self.world)
                    if fallback_action:
                        final_action_to_take = fallback_action
                        logger.info("[Tick %s][AI Agent %s] Internal BT fallback action: '%s'", tm.tick_counter, entity_id, fallback_action)
            
            if final_action_to_take:
                if final_action_to_take.upper().startswith("GENERATE_ABILITY"):
                    final_action_to_take, angel_step_context = self._contextualize_generate_ability(final_action_to_take, ai_comp, entity_id)
                    if ai_comp and angel_step_context: 
                        ai_comp.newly_generated_ability_context = angel_step_context
                
                logger.info("[Tick %s][AI Agent %s] Final Enqueued Action: '%s'", tm.tick_counter, entity_id, final_action_to_take.replace("\n", "//"))
                parsed_actions_list = parse_action_string(entity_id, final_action_to_take)
                for act_obj in parsed_actions_list:
                    self.action_queue._queue.append(act_obj)
                ai_comp.last_llm_action_tick = tm.tick_counter
            
            elif ai_comp.pending_llm_prompt_id is None: 
                logger.debug("[Tick %s][AI Agent %s] No action decided, not waiting. Effective idle. Cooldown applies.", tm.tick_counter, entity_id)
                ai_comp.last_llm_action_tick = tm.tick_counter
            
            # Moved clearing of last_error to after prompt_builder might use it
            if ai_comp.last_error:
                ai_comp.last_error = None


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