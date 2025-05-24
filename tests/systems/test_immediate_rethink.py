import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem


class DummyLLM:
    mode = "offline"


def test_immediate_rethink_bypasses_cooldown():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.llm_manager_instance = DummyLLM()
    world.async_llm_responses = {}

    actions = []
    system = AIReasoningSystem(world, world.llm_manager_instance, actions)

    agent_id = world.entity_manager.create_entity()
    state = AIState(personality="tester")
    world.component_manager.add_component(agent_id, state)

    world.time_manager.tick_counter = 0
    state.last_llm_action_tick = 0
    state.needs_immediate_rethink = True

    world.time_manager.tick_counter = 1
    system.update(1)

    assert state.needs_immediate_rethink is False
    assert state.last_llm_action_tick == 1
    assert actions, "Expected an action produced when immediate rethink is set"
