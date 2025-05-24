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
from agent_world.core.components.physics import Physics
import pytest
from typing import Any


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


def test_move_blocked_event_when_occupied():
    world = World((3, 3))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(cell_size=1)

    log: list[dict[str, Any]] = []
    movement = MovementSystem(world, event_log=log)

    mover = world.entity_manager.create_entity()
    blocker = world.entity_manager.create_entity()

    world.component_manager.add_component(mover, Position(0, 0))
    world.component_manager.add_component(mover, Velocity(1, 0))
    world.spatial_index.insert(mover, (0, 0))

    world.component_manager.add_component(blocker, Position(1, 0))
    world.spatial_index.insert(blocker, (1, 0))

    movement.update()

    pos = world.component_manager.get_component(mover, Position)
    assert (pos.x, pos.y) == (0, 0)
    assert log[-1] == {"type": "move_blocked", "entity": mover, "pos": (1, 0)}


def test_physics_dataclass():
    p = Physics(mass=1.0, vx=2.0, vy=-1.0, friction=0.5)
    assert (p.mass, p.vx, p.vy, p.friction) == (1.0, 2.0, -1.0, 0.5)


def test_movement_uses_physics_when_velocity_missing():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(cell_size=1)

    movement = MovementSystem(world)
    e = world.entity_manager.create_entity()
    phys = Physics(mass=1.0, vx=1.2, vy=0.0, friction=0.5)
    world.component_manager.add_component(e, Position(0, 0))
    world.component_manager.add_component(e, phys)
    world.spatial_index.insert(e, (0, 0))

    movement.update()

    pos = world.component_manager.get_component(e, Position)
    assert (pos.x, pos.y) == (1, 0)
    updated = world.component_manager.get_component(e, Physics)
    assert updated.vx == pytest.approx(0.6)
    assert updated.vy == 0.0
