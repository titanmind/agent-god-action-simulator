from agent_world.systems.movement.pathfinding import a_star


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_a_star_simple_line():
    start = (0, 0)
    goal = (3, 0)
    path = a_star(start, goal)
    assert path[0] == start
    assert path[-1] == goal
    assert len(path) == 4
    for p1, p2 in zip(path, path[1:]):
        assert _manhattan(p1, p2) == 1


def test_a_star_diagonal():
    start = (0, 0)
    goal = (2, 1)
    path = a_star(start, goal)
    assert path[0] == start
    assert path[-1] == goal
    assert len(path) == _manhattan(start, goal) + 1


def test_a_star_same_start_goal():
    start = (1, 2)
    path = a_star(start, start)
    assert path == [start]
