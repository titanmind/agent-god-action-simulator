from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.position import Position
from agent_world.core.components.physics import Physics
from agent_world.utils.cli import commands
import agent_world.systems.ai.actions as actions


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(1)
    return world


def test_actions_module_has_no_player_id_constant():
    assert not hasattr(actions, "PLAYER_ID")


def test_spawn_does_not_modify_entity_zero():
    world = _setup_world()
    # Simulate a legacy player entity with ID 0
    world.entity_manager._entity_components[0] = {}
    world.component_manager._components[0] = {}

    spawned_id = commands.spawn(world, "npc")
    assert spawned_id is not None

    cm = world.component_manager
    assert cm.get_component(0, Position) is None
    assert cm.get_component(0, Physics) is None
    assert 0 not in world.spatial_index._entity_pos
