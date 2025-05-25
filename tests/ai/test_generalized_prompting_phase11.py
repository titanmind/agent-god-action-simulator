from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState, Goal
from agent_world.core.components.position import Position
from agent_world.core.components.inventory import Inventory
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.systems.interaction.pickup import Tag
from agent_world.ai.prompt_builder import build_prompt


class DummyAbilitySystem:
    def __init__(self):
        self.abilities = {"MeleeStrike": object()}


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.ability_system_instance = DummyAbilitySystem()
    return world


def test_prompt_lists_goals_without_critical_text():
    world = _setup_world()
    agent = world.entity_manager.create_entity()
    goal = Goal(type="acquire", target=3)
    world.component_manager.add_component(agent, AIState(personality="bot", goals=[goal]))

    prompt = build_prompt(agent, world)

    assert "acquire 3" in prompt
    assert "CRITICAL SITUATION" not in prompt


def test_prompt_includes_visible_item_info():
    world = _setup_world()
    agent = world.entity_manager.create_entity()
    item = world.entity_manager.create_entity()
    world.component_manager.add_component(agent, AIState(personality="bot"))
    world.component_manager.add_component(agent, Position(0, 0))
    world.component_manager.add_component(item, Position(1, 0))
    world.component_manager.add_component(item, Tag("item"))
    world.component_manager.add_component(agent, PerceptionCache(visible=[item], last_tick=0))
    world.component_manager.add_component(agent, Inventory(capacity=5))

    prompt = build_prompt(agent, world)

    assert str(item) in prompt
    assert "visible_entities_and_items" in prompt

