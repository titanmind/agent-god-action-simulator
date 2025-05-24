from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.components.physics import Physics
from agent_world.systems.movement.physics_system import PhysicsSystem, Force
from agent_world.systems.movement.pathfinding import set_obstacles, clear_obstacles
from agent_world.core.spatial.spatial_index import SpatialGrid


def _make_world():
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    w.spatial_index = SpatialGrid(cell_size=1)
    return w


def test_force_integration():
    world = _make_world()
    phys_sys = PhysicsSystem(world)

    e = world.entity_manager.create_entity()
    phys = Physics(mass=1.0, vx=0.0, vy=0.0, friction=1.0)
    world.component_manager.add_component(e, phys)
    world.component_manager.add_component(e, Force(2.0, 1.0))

    phys_sys.update()

    updated = world.component_manager.get_component(e, Physics)
    assert (updated.vx, updated.vy) == (2.0, 1.0)
    assert world.component_manager.get_component(e, Force) is None


def test_collision_zeroes_velocity():
    world = _make_world()
    phys_sys = PhysicsSystem(world)

    e = world.entity_manager.create_entity()
    world.component_manager.add_component(e, Position(0, 0))
    world.component_manager.add_component(
        e, Physics(mass=1.0, vx=0.0, vy=0.0, friction=1.0)
    )
    world.component_manager.add_component(e, Force(1.0, 0.0))
    set_obstacles({(1, 0)})

    phys_sys.update()
    clear_obstacles()

    phys = world.component_manager.get_component(e, Physics)
    assert phys.vx == 0.0 and phys.vy == 0.0
