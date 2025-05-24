from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.role import RoleComponent
from agent_world.ai.prompt_builder import build_prompt


class DummyAbilitySystem:
    def __init__(self):
        self.abilities = {"Fireball": object()}


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.ability_system_instance = DummyAbilitySystem()
    return world


def test_prompt_hides_generation_when_role_forbids():
    world = _setup_world()
    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="t"))
    world.component_manager.add_component(
        agent_id, RoleComponent("npc", can_request_abilities=False)
    )

    prompt = build_prompt(agent_id, world)
    assert "GENERATE_ABILITY" not in prompt
    assert "ABILITIES YOU KNOW" not in prompt


def test_prompt_includes_generation_by_default():
    world = _setup_world()
    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="t"))

    prompt = build_prompt(agent_id, world)
    assert "GENERATE_ABILITY" in prompt
    assert "ABILITIES YOU KNOW" in prompt
