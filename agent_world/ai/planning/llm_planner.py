from __future__ import annotations

"""LLM-backed planner for generating action plans."""

from typing import Any, List

from .base_planner import BasePlanner
from ..llm.llm_manager import LLMManager
from ...core.components.ai_state import Goal, ActionStep


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
            parts = line.split()
            action = parts[0]
            target = None
            params: dict[str, Any] = {}
            if len(parts) > 1:
                arg = parts[1]
                if arg.isdigit():
                    target = int(arg)
                else:
                    params["arg"] = arg
            steps.append(ActionStep(action=action, target=target, parameters=params))
        return steps

    def create_plan(self, agent_id: int, goals: List[Goal], world: Any) -> List[ActionStep]:
        goal_lines = [f"- {g.type}{(' ' + str(g.target)) if g.target is not None else ''}" for g in goals]
        goal_text = "\n".join(goal_lines) if goal_lines else "None"
        prompt = (
            f"Plan steps for agent {agent_id} to achieve the following goals:\n{goal_text}\n"
            "Respond with one action step per line in the format 'ACTION [arg]'"
        )
        response = self.llm.request(prompt, world, model=self.llm.agent_decision_model)
        if not response or response.startswith("<"):
            return []
        return self._parse_plan_text(response)


__all__ = ["LLMPlanner"]
