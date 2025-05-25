from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.role import RoleComponent
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.ai.behavior_tree_system import BehaviorTreeSystem
from agent_world.ai.behaviors.generic_bt import (
    build_resource_gather_tree,
    build_flee_low_health_tree,
    build_item_interaction_tree,
)
from agent_world.systems.interaction.pickup import Tag


def _setup_world() -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.spatial_index = SpatialGrid(cell_size=1)
    world.raw_actions_with_actor = []
    return world


def test_gather_tree_moves_and_harvests():
    world = _setup_world()
    tree = build_resource_gather_tree()
    system = BehaviorTreeSystem(world, default_tree=tree)

    agent = world.entity_manager.create_entity()
    cm = world.component_manager
    cm.add_component(agent, AIState(personality="bot"))
    cm.add_component(agent, RoleComponent("worker", uses_llm=False))
    cm.add_component(agent, Position(0, 1))

    world.tile_map[1][2] = {"kind": "ore"}

    system.update(0)
    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor.pop()
    assert actor == agent
    assert action == "MOVE E"

    cm.get_component(agent, Position).x = 2
    system.update(1)
    actor, action = world.raw_actions_with_actor.pop()
    assert action.startswith("HARVEST")


def test_flee_tree_moves_away_from_enemy():
    world = _setup_world()
    tree = build_flee_low_health_tree()
    system = BehaviorTreeSystem(world, default_tree=tree)

    agent = world.entity_manager.create_entity()
    enemy = world.entity_manager.create_entity()
    cm = world.component_manager
    cm.add_component(agent, AIState(personality="bot"))
    cm.add_component(agent, RoleComponent("scout", uses_llm=False))
    cm.add_component(agent, Position(1, 1))
    cm.add_component(agent, Health(cur=2, max=10))
    world.spatial_index.insert(agent, (1, 1))

    cm.add_component(enemy, Position(2, 1))
    cm.add_component(enemy, Health(cur=5, max=5))
    world.spatial_index.insert(enemy, (2, 1))

    system.update(0)
    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor.pop()
    assert actor == agent
    assert action == "MOVE W"


def test_item_interaction_pickup():
    world = _setup_world()
    tree = build_item_interaction_tree()
    system = BehaviorTreeSystem(world, default_tree=tree)

    agent = world.entity_manager.create_entity()
    item = world.entity_manager.create_entity()
    cm = world.component_manager
    cm.add_component(agent, AIState(personality="bot"))
    cm.add_component(agent, RoleComponent("scout", uses_llm=False))
    cm.add_component(agent, Position(0, 0))
    world.spatial_index.insert(agent, (0, 0))

    cm.add_component(item, Position(0, 0))
    cm.add_component(item, Tag("item"))
    world.spatial_index.insert(item, (0, 0))

    system.update(0)
    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor.pop()
    assert actor == agent
    assert action == f"PICKUP {item}"
