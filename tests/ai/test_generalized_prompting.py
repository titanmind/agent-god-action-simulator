import pytest

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.core.components.position import Position
from agent_world.systems.movement.pathfinding import OBSTACLES, set_obstacles
from agent_world.scenarios.default_pickup_scenario import DefaultPickupScenario
from agent_world.ai.prompt_builder import build_prompt


class DummyAbilitySystem:
    def __init__(self):
        self.abilities = {"DisintegrateObstacle": object()}


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.spatial_index = SpatialGrid(1)
    world.ability_system_instance = DummyAbilitySystem()
    return world


def _get_agent_and_item_ids(world: World):
    em = world.entity_manager
    cm = world.component_manager
    ids = sorted(em.all_entities.keys())
    agent_id = ids[0] if cm.get_component(ids[0], AIState) else ids[1]
    item_id = ids[1] if agent_id == ids[0] else ids[0]
    return agent_id, item_id


def test_prompt_reports_obstacle_coordinates():
    world = _setup_world()
    DefaultPickupScenario().setup(world)
    agent_id, item_id = _get_agent_and_item_ids(world)

    # make item visible
    cache = world.component_manager.get_component(agent_id, PerceptionCache)
    if cache:
        cache.visible = [item_id]

    prompt = build_prompt(agent_id, world)

    obstacle = next(iter(OBSTACLES))
    assert "CRITICAL OBSTACLE" in prompt
    assert str(obstacle) in prompt


def test_prompt_updates_when_obstacle_moves():
    world = _setup_world()
    DefaultPickupScenario().setup(world)
    agent_id, item_id = _get_agent_and_item_ids(world)

    cache = world.component_manager.get_component(agent_id, PerceptionCache)
    if cache:
        cache.visible = [item_id]

    agent_pos = world.component_manager.get_component(agent_id, Position)
    item_pos = world.component_manager.get_component(item_id, Position)

    # Move item east and place obstacle in new path
    item_pos.x = agent_pos.x + 2
    item_pos.y = agent_pos.y
    set_obstacles([(agent_pos.x + 1, agent_pos.y)])

    prompt = build_prompt(agent_id, world)
    assert str((agent_pos.x + 1, agent_pos.y)) in prompt
    assert "East" in prompt
