import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.role import RoleComponent
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem


class DummyLLM:
    def __init__(self):
        self.mode = "live"
        self.prompts = []

    def request(self, prompt: str, world: World) -> str:
        self.prompts.append(prompt)
        return "MOVE N"


def _setup_world(llm: DummyLLM) -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.llm_manager_instance = llm
    world.async_llm_responses = {}
    world.raw_actions_with_actor = []
    return world


def test_role_disables_llm_use():
    llm = DummyLLM()
    world = _setup_world(llm)
    system = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="bot"))
    world.component_manager.add_component(agent_id, RoleComponent("worker", uses_llm=False))

    world.time_manager.tick_counter = 0
    system.update(0)

    assert not llm.prompts, "LLM should not be called when role disables it"
    assert world.raw_actions_with_actor, "Behavior tree action expected"
    actor, action = world.raw_actions_with_actor[0]
    assert actor == agent_id
    assert action.startswith("MOVE")


def test_prompt_suppresses_generate_ability():
    llm = DummyLLM()
    world = _setup_world(llm)
    system = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="bot"))
    world.component_manager.add_component(agent_id, RoleComponent("scout", can_request_abilities=False))

    world.time_manager.tick_counter = 0
    system.update(0)

    assert llm.prompts, "LLM should be used when allowed"
    sent_prompt = llm.prompts[0]
    assert "GENERATE_ABILITY" not in sent_prompt
    assert world.raw_actions_with_actor[0][1] == "MOVE N"
