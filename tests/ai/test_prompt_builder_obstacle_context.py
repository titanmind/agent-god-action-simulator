from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState, Goal
from agent_world.core.components.position import Position
from agent_world.core.components.inventory import Inventory
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.systems.movement import pathfinding
from agent_world.ai.prompt_builder import build_prompt


class DummyAbilitySystem:
    def __init__(self):
        self.abilities = {}


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.ability_system_instance = DummyAbilitySystem()
    return world


def test_prompt_includes_obstacle_note():
    world = _setup_world()
    agent_id = world.entity_manager.create_entity()
    item_id = world.entity_manager.create_entity()

    world.component_manager.add_component(agent_id, Position(2, 2))
    world.component_manager.add_component(agent_id, Inventory(capacity=5))
    world.component_manager.add_component(agent_id, PerceptionCache())
    world.component_manager.add_component(
        agent_id, AIState(personality="t", goals=[Goal("acquire", item_id)])
    )

    world.component_manager.add_component(item_id, Position(2, 0))

    pathfinding.set_obstacles([(2, 1)])

    prompt = build_prompt(agent_id, world)

    assert "SYSTEM NOTE: Your direct path" in prompt
    assert "(2, 1)" in prompt
    pathfinding.clear_obstacles()

