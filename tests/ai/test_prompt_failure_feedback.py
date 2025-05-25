from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.ai.prompt_builder import build_prompt


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    return world


def test_prompt_includes_error_note():
    world = _setup_world()
    agent_id = world.entity_manager.create_entity()
    ai_state = AIState(personality="t")
    ai_state.last_error = "boom"
    world.component_manager.add_component(agent_id, ai_state)

    prompt = build_prompt(agent_id, world)

    assert prompt.startswith("SYSTEM NOTE: boom")


def test_prompt_no_note_when_no_error():
    world = _setup_world()
    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="t"))

    prompt = build_prompt(agent_id, world)

    assert not prompt.startswith("SYSTEM NOTE:")
