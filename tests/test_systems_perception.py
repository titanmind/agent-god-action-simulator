from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.systems.perception.perception_system import PerceptionSystem
from agent_world.systems.perception.line_of_sight import has_line_of_sight


def test_has_line_of_sight_distance_check():
    a = Position(0, 0)
    b = Position(3, 4)
    assert has_line_of_sight(a, b, 5)
    assert not has_line_of_sight(a, b, 4)


def test_perception_cache_population():
    world = World((10, 10))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(cell_size=1)

    em = world.entity_manager
    cm = world.component_manager

    e1 = em.create_entity()
    e2 = em.create_entity()

    cm.add_component(e1, Position(0, 0))
    cm.add_component(e1, PerceptionCache())
    cm.add_component(e2, Position(1, 1))

    world.spatial_index.insert(e1, (0, 0))
    world.spatial_index.insert(e2, (1, 1))

    system = PerceptionSystem(world, view_radius=5)
    system.update(tick=1)

    cache = cm.get_component(e1, PerceptionCache)
    assert cache.visible == [e2]
    assert cache.last_tick == 1
