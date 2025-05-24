from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.systems.movement.movement_system import MovementSystem, Velocity


def test_velocity_dataclass():
    v = Velocity(2, -1)
    assert (v.dx, v.dy) == (2, -1)


def test_movement_updates_position_and_index():
    world = World((10, 10))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(cell_size=1)

    system = MovementSystem(world)
    entity = world.entity_manager.create_entity()
    world.component_manager.add_component(entity, Position(0, 0))
    world.component_manager.add_component(entity, Velocity(1, 1))
    world.spatial_index.insert(entity, (0, 0))

    system.update()

    pos = world.component_manager.get_component(entity, Position)
    assert (pos.x, pos.y) == (1, 1)
    assert world.spatial_index.query_radius((1, 1), 0) == [entity]
    assert world.spatial_index.query_radius((0, 0), 0) == []
