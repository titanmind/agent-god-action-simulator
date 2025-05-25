import pytest
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.world import World
from agent_world.core.components.ai_state import AIState, Goal
from agent_world.core.components.position import Position
from agent_world.ai.planning.llm_planner import LLMPlanner
from agent_world.systems.movement.pathfinding import set_obstacles, clear_obstacles


class DummyLLM:
    def __init__(self):
        self.mode = "live"
        self.prompts = []
        self.agent_decision_model = "test-model"

    def request(self, prompt: str, world, *, model: str | None = None):
        self.prompts.append(prompt)
        return "DEAL_WITH_OBSTACLE 2,1\nMOVE N"


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    return world


def test_planner_adds_obstacle_step():
    clear_obstacles()
    llm = DummyLLM()
    planner = LLMPlanner(llm)
    world = _setup_world()

    agent = world.entity_manager.create_entity()
    item = world.entity_manager.create_entity()

    world.component_manager.add_component(agent, Position(2, 2))
    world.component_manager.add_component(item, Position(2, 0))
    ai_state = AIState(personality="bot", goals=[Goal("acquire", target=item)])
    world.component_manager.add_component(agent, ai_state)

    set_obstacles([(2, 1)])

    steps = planner.create_plan(agent, ai_state.goals, world)

    assert llm.prompts, "Planner did not send prompt to LLM"
    assert "obstacle" in llm.prompts[0].lower()
    assert steps and steps[0].action == "DEAL_WITH_OBSTACLE"
    assert steps[0].step_type == "deal_with_obstacle"
    assert steps[0].parameters.get("coords") == (2, 1)

