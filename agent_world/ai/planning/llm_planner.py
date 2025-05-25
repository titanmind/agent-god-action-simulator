from __future__ import annotations

"""LLM-backed planner for generating action plans."""

from typing import Any, List, Tuple
import re
import time

from .base_planner import BasePlanner
from ..llm.llm_manager import LLMManager
from ...core.components.ai_state import Goal, ActionStep
from ...core.components.position import Position
from ...systems.movement.pathfinding import is_blocked


class LLMPlanner(BasePlanner):
    """Use an LLM to convert goals into a list of :class:`ActionStep`."""

    def __init__(self, llm: LLMManager) -> None:
        self.llm = llm

    def _parse_plan_text(self, text: str) -> List[ActionStep]:
        steps: List[ActionStep] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            
            original_line = line # Keep original for potential full arg if no specific parsing matches
            
            # Check if line starts with "ACTION " and remove it for parsing
            if line.upper().startswith("ACTION "):
                line = line[len("ACTION "):].strip()

            parts = line.split(maxsplit=1)
            action_verb = parts[0].upper() # Use upper for matching, store as is or upper in ActionStep
            
            target = None
            params: dict[str, Any] = {}
            step_type: str | None = None
            rest = parts[1] if len(parts) > 1 else ""

            # Set step_type based on common planning verbs
            if action_verb == "DEAL_WITH_OBSTACLE":
                step_type = "deal_with_obstacle" # Consistent lowercase
                coords_str = rest.strip().strip("()")
                if "," in coords_str:
                    x_str, y_str = coords_str.split(",", 1)
                    try:
                        params["coords"] = (int(x_str.strip()), int(y_str.strip()))
                    except ValueError:
                        params["coords_str"] = coords_str # Store as string if not parsable
                elif coords_str: # If it's just one thing, might be an ID or malformed
                    params["obstacle_ref"] = coords_str

            elif action_verb == "GENERATE_ABILITY":
                step_type = "generate_ability" # Consistent lowercase
                desc = rest.strip()
                # Remove potential quotes if LLM adds them
                if (desc.startswith("'") and desc.endswith("'")) or \
                   (desc.startswith('"') and desc.endswith('"')):
                    desc = desc[1:-1]
                if desc:
                    params["description"] = desc
            
            elif action_verb == "MOVE_TO": # Example of another planned action
                step_type = "move_to"
                # Try to parse target as int (ID) or tuple (coords)
                arg = rest.strip()
                if arg.isdigit():
                    target = int(arg)
                elif "(" in arg and "," in arg and ")" in arg:
                    try:
                        coords_part = arg.strip().strip("()")
                        x_str, y_str = coords_part.split(",",1)
                        params["target_coords"] = (int(x_str.strip()), int(y_str.strip()))
                    except ValueError:
                        params["target_str"] = arg # Store as string if malformed
                elif arg: # If just a string, could be a named location or item reference
                    params["target_ref"] = arg

            else: # Generic action, could be MOVE, PICKUP, USE_ABILITY etc.
                  # The AIReasoningSystem will prompt LLM for these.
                step_type = action_verb.lower() # Store the action verb as step_type
                # For generic actions, the 'rest' might be a target ID or more complex args.
                # We'll let the AIReasoningSystem's LLM call figure out the specifics
                # based on this step.
                if rest.isdigit():
                    target = int(rest)
                elif rest:
                    params["arg"] = rest
                # If the original line started with "ACTION ", action_verb is already correct.
                # If not, the original_line itself might be the action string.
                # We use action_verb as the primary identifier.

            steps.append(
                ActionStep(action=action_verb, target=target, parameters=params, step_type=step_type)
            )
        return steps

    @staticmethod
    def _first_obstacle_in_direct_path(start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[int, int] | None:
        x, y = start
        gx, gy = goal
        while x != gx:
            x += 1 if gx > x else -1
            if is_blocked((x, y)):
                return (x, y)
        while y != gy:
            y += 1 if gy > y else -1
            if is_blocked((x, y)):
                return (x, y)
        return None

    def create_plan(self, agent_id: int, goals: List[Goal], world: Any) -> List[ActionStep]:
        goal_lines = [f"- {g.type}{(' ' + str(g.target)) if g.target is not None else ''}" for g in goals]
        goal_text = "\n".join(goal_lines) if goal_lines else "None"

        obstacle_note = ""
        if world and goals:
            cm = getattr(world, "component_manager", None)
            if cm:
                agent_pos = cm.get_component(agent_id, Position)
                # Assuming the first goal is the primary one for obstacle checking
                if goals[0].target is not None:
                    goal_target_id_or_coords = goals[0].target 
                    
                    target_coords_tuple: Tuple[int, int] | None = None
                    if isinstance(goal_target_id_or_coords, int): # if it's an entity ID
                        target_pos_comp = cm.get_component(goal_target_id_or_coords, Position)
                        if target_pos_comp:
                            target_coords_tuple = (target_pos_comp.x, target_pos_comp.y)
                    elif isinstance(goal_target_id_or_coords, (tuple, list)) and len(goal_target_id_or_coords) == 2:
                        try:
                            target_coords_tuple = (int(goal_target_id_or_coords[0]), int(goal_target_id_or_coords[1]))
                        except ValueError:
                            pass # Not valid coords

                    if agent_pos and target_coords_tuple:
                        obs = self._first_obstacle_in_direct_path(
                            (agent_pos.x, agent_pos.y), target_coords_tuple
                        )
                        if obs:
                            ox, oy = obs
                            obstacle_note = (
                                f"Your path to goal target {goal_target_id_or_coords} at {target_coords_tuple} is blocked by an obstacle at ({ox},{oy}).\n"
                                "Include a step such as 'DEAL_WITH_OBSTACLE "
                                f"{ox},{oy}' or 'GENERATE_ABILITY 'description to remove obstacle at {ox},{oy}'' if appropriate.\n"
                            )

        prompt = (
            f"Plan steps for agent {agent_id} to achieve the following goals:\n{goal_text}\n"
            f"{obstacle_note}"
            "Respond with one action step per line in the format 'ACTION [arg]' or 'VERB [arg]'. Examples: 'MOVE_TO (X,Y)', 'DEAL_WITH_OBSTACLE (X,Y)', 'GENERATE_ABILITY description'."
        )
        response = self.llm.request(prompt, world, model=self.llm.agent_decision_model)

        if not response or response.startswith("<"): # e.g. <wait>, <error_...>
            return []

        plan_text = ""
        # Check if the response is a 32-char hex string (likely a prompt_id for async)
        if re.fullmatch(r"[a-f0-9]{32}", response) and world is not None:
            fut = getattr(world, "async_llm_responses", {}).get(response)
            if fut is not None:
                start_time = time.time() # Corrected variable name
                # Wait for the future to be done, with a timeout (e.g., 5 seconds)
                while not fut.done() and time.time() - start_time < 5.0: # Ensure float for time comparison
                    time.sleep(0.01) # Polling, consider async await if planner can be async
                
                if fut.done():
                    try:
                        plan_text = fut.result() # Get the actual plan text
                    except Exception:
                        plan_text = "" # Handle potential errors getting the result
                else: # Future timed out
                    plan_text = ""
                
                # Clean up the future from the world's dictionary in either case
                getattr(world, "async_llm_responses", {}).pop(response, None)
        else:
            # If the response was not a prompt_id, assume it's the plan text directly
            plan_text = response

        if not plan_text or plan_text.startswith("<"):
            return []
        return self._parse_plan_text(plan_text)


__all__ = ["LLMPlanner"]