from agent_world.core.components.ai_state import AIState, Goal, ActionStep
from agent_world.ai.planning.base_planner import BasePlanner


class DummyPlanner(BasePlanner):
    def create_plan(self, agent_id: int, goals: list[Goal], world: object) -> list[ActionStep]:
        return []


def test_ai_state_fields():
    state = AIState(personality="bot")
    assert isinstance(state.goals, list)
    assert isinstance(state.current_plan, list)


def test_base_planner_subclass():
    planner = DummyPlanner()
    assert planner.create_plan(1, [], object()) == []
