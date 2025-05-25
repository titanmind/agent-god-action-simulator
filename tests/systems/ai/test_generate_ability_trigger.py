import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState, Goal, ActionStep
from agent_world.core.components.position import Position
from agent_world.systems.ai.actions import ActionQueue
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem, RawActionCollector
from agent_world.systems.movement.pathfinding import set_obstacles, clear_obstacles


class DummyLLM:
    mode = "live"

    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts = []
        self.agent_decision_model = "test-model"

    def request(self, prompt: str, world: World, *, model: str | None = None) -> str:
        self.prompts.append(prompt)
        return self.response


def _setup_world(llm: DummyLLM) -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.llm_manager_instance = llm
    world.action_queue = ActionQueue()
    world.raw_actions_with_actor = RawActionCollector(world.action_queue)
    world.async_llm_responses = {}
    return world


def test_contextualize_generate_ability_from_plan_step():
    llm = DummyLLM("GENERATE_ABILITY remove obstacle")
    world = _setup_world(llm)
    ai_sys = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    step = ActionStep(
        action="WAIT",
        step_type="DEAL_WITH_OBSTACLE",
        parameters={"obstacle": "(2,1)", "goal": "(2,0)"},
    )
    ai_state = AIState(personality="bot", current_plan=[step])
    world.component_manager.add_component(agent, ai_state)

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor[0]
    assert actor == agent
    assert action.startswith("GENERATE_ABILITY")
    assert "(2,1)" in action
    assert "(2,0)" in action


def test_contextualize_generate_ability_general_obstacle():
    llm = DummyLLM("GENERATE_ABILITY remove obstacle")
    world = _setup_world(llm)
    ai_sys = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    item = world.entity_manager.create_entity()
    world.component_manager.add_component(agent, Position(2, 2))
    world.component_manager.add_component(item, Position(2, 0))
    goal = Goal("acquire", target=item)
    world.component_manager.add_component(agent, AIState(personality="bot", goals=[goal]))

    set_obstacles([(2, 1)])

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor[0]
    assert actor == agent
    assert action.startswith("GENERATE_ABILITY")
    assert "(2,1)" in action
    assert "(2,0)" in action

    clear_obstacles()
