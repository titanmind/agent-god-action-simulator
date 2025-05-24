# tests/test_movement_and_pathfinding.py
"""
Combined tests for path-finding (A*) and basic movement/velocity integration.
Both feature sets were introduced in separate branches and are now reconciled
into a single, conflict-free test module.
"""

# ---------- Path-finding -----------------------------------------------------

from agent_world.systems.movement.pathfinding import (
    a_star,
    set_obstacles,
    clear_obstacles,
)


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Cheaper‐than‐euclidean heuristic used by the A* implementation."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_a_star_simple_line():
    start, goal = (0, 0), (3, 0)
    path = a_star(start, goal)
    assert path[0] == start and path[-1] == goal
    assert len(path) == 4
    assert all(_manhattan(p1, p2) == 1 for p1, p2 in zip(path, path[1:]))


def test_a_star_diagonal():
    start, goal = (0, 0), (2, 1)
    path = a_star(start, goal)
    assert path[0] == start and path[-1] == goal
    assert len(path) == _manhattan(start, goal) + 1


def test_a_star_same_start_goal():
    start = (1, 2)
    assert a_star(start, start) == [start]


def test_a_star_with_obstacle():
    set_obstacles({(1, 0)})
    path = a_star((0, 0), (2, 0))
    clear_obstacles()
    assert path[0] == (0, 0) and path[-1] == (2, 0)
    assert (1, 0) not in path


# ---------- Movement / Velocity ---------------------------------------------

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
    # world scaffold
    world = World((10, 10))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(cell_size=1)

    # system + entity setup
    movement = MovementSystem(world)
    e = world.entity_manager.create_entity()
    world.component_manager.add_component(e, Position(0, 0))
    world.component_manager.add_component(e, Velocity(1, 1))
    world.spatial_index.insert(e, (0, 0))

    # one tick
    movement.update()

    pos = world.component_manager.get_component(e, Position)
    assert (pos.x, pos.y) == (1, 1)
    assert world.spatial_index.query_radius((1, 1), 0) == [e]
    assert world.spatial_index.query_radius((0, 0), 0) == []


def test_movement_blocked_by_obstacle():
    world = World((3, 3))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(cell_size=1)

    movement = MovementSystem(world)
    e = world.entity_manager.create_entity()
    world.component_manager.add_component(e, Position(0, 0))
    world.component_manager.add_component(e, Velocity(1, 0))
    world.spatial_index.insert(e, (0, 0))

    set_obstacles({(1, 0)})

    movement.update()

    pos = world.component_manager.get_component(e, Position)
    assert (pos.x, pos.y) == (0, 0)
    assert world.spatial_index.query_radius((0, 0), 0) == [e]
    clear_obstacles()
