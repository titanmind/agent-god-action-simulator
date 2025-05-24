"""Basic grid-based pathfinding helpers."""

from __future__ import annotations

from heapq import heappop, heappush
from typing import Dict, List, Tuple


Coord = Tuple[int, int]


def _heuristic(a: Coord, b: Coord) -> float:
    """Return estimated distance between two points.

    This uses Manhattan distance which works well for a 4-neighbour grid.
    """

    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbors(node: Coord) -> List[Coord]:
    """Return the cardinal neighbours of ``node``."""

    x, y = node
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def _reconstruct(came_from: Dict[Coord, Coord], current: Coord) -> List[Coord]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def a_star(start: Coord, goal: Coord) -> List[Coord]:
    """Return the shortest path from ``start`` to ``goal`` using A*.

    With no obstacles this reduces to a straight Manhattan path but the
    algorithm is kept general for future extension.
    """

    if start == goal:
        return [start]

    open_set: List[Tuple[float, float, Coord]] = []
    heappush(open_set, (_heuristic(start, goal), 0.0, start))

    came_from: Dict[Coord, Coord] = {}
    g_score: Dict[Coord, float] = {start: 0.0}
    closed: set[Coord] = set()

    while open_set:
        f, g, current = heappop(open_set)

        if current == goal:
            return _reconstruct(came_from, current)

        if current in closed:
            continue
        closed.add(current)

        for n in _neighbors(current):
            tentative_g = g + 1
            if n in closed:
                continue
            if tentative_g < g_score.get(n, float("inf")):
                came_from[n] = current
                g_score[n] = tentative_g
                f_score = tentative_g + _heuristic(n, goal)
                heappush(open_set, (f_score, tentative_g, n))

    # If no path is found (should not happen with no obstacles), return empty
    return []


__all__ = ["a_star"]

