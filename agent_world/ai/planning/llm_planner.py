from __future__ import annotations

"""LLM-backed planner for generating action plans."""

from typing import Any, List, Tuple

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
            parts = line.split(maxsplit=1)
            action = parts[0]
            target = None
            params: dict[str, Any] = {}
            step_type: str | None = None
            rest = parts[1] if len(parts) > 1 else ""

            if action == "DEAL_WITH_OBSTACLE":
                step_type = "deal_with_obstacle"
                coords = rest.strip().strip("()")
                if "," in coords:
                    x_str, y_str = coords.split(",", 1)
                    try:
                        params["coords"] = (int(x_str), int(y_str))
                    except ValueError:
                        params["coords"] = coords
                elif coords:
                    params["coords"] = coords
            elif action == "GENERATE_ABILITY":
                step_type = "generate_ability"
                desc = rest.strip()
                if desc.startswith("'") and desc.endswith("'") and len(desc) >= 2:
                    desc = desc[1:-1]
                if desc:
                    params["description"] = desc
            else:
                arg = rest.strip()
                if arg:
                    if arg.isdigit():
                        target = int(arg)
                    else:
                        params["arg"] = arg

            steps.append(
                ActionStep(action=action, target=target, parameters=params, step_type=step_type)
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
                goal_target = goals[0].target
                if agent_pos and goal_target is not None:
                    target_pos = cm.get_component(goal_target, Position)
                    if target_pos:
                        obs = self._first_obstacle_in_direct_path(
                            (agent_pos.x, agent_pos.y), (target_pos.x, target_pos.y)
                        )
                        if obs:
                            ox, oy = obs
                            obstacle_note = (
                                f"Your path to goal target {goal_target} is blocked by an obstacle at ({ox},{oy}).\n"
                                "Include a step such as 'DEAL_WITH_OBSTACLE "
                                f"{ox},{oy}' or 'GENERATE_ABILITY 'description to remove obstacle at {ox},{oy}'' if appropriate.\n"
                            )

        prompt = (
            f"Plan steps for agent {agent_id} to achieve the following goals:\n{goal_text}\n"
            f"{obstacle_note}"
            "Respond with one action step per line in the format 'ACTION [arg]'"
        )
        response = self.llm.request(prompt, world, model=self.llm.agent_decision_model)
        if not response or response.startswith("<"):
            return []
        return self._parse_plan_text(response)


__all__ = ["LLMPlanner"]
