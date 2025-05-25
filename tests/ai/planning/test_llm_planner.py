from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState, Goal
from agent_world.core.components.role import RoleComponent
from agent_world.ai.planning.llm_planner import LLMPlanner
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem


class DummyLLM:
    def __init__(self):
        self.mode = "live"
        self.prompts = []
        self.agent_decision_model = "test-model"

    def request(self, prompt: str, world: World, *, model: str | None = None):
        self.prompts.append(prompt)
        if "Plan" in prompt:
            return "MOVE N"
        return "IDLE"


def _setup_world(llm: DummyLLM) -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.llm_manager_instance = llm
    world.async_llm_responses = {}
    world.raw_actions_with_actor = []
    return world


def test_llm_planner_creates_steps():
    llm = DummyLLM()
    planner = LLMPlanner(llm)
    world = World((5, 5))
    steps = planner.create_plan(1, [Goal("test", 1)], world)
    assert steps and steps[0].action == "MOVE"
    assert steps[0].parameters.get("arg") == "N"


def test_reasoning_system_uses_plan():
    llm = DummyLLM()
    world = _setup_world(llm)
    system = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    state = AIState(personality="p", goals=[Goal("move")])
    world.component_manager.add_component(agent, state)
    world.component_manager.add_component(agent, RoleComponent("npc"))

    world.time_manager.tick_counter = 0
    system.update(0)

    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor[0]
    assert actor == agent
    assert action == "MOVE N"
    # planner prompt should have been called once
    assert len(llm.prompts) == 1
