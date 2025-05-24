from __future__ import annotations

from typing import List, Tuple

from .spatial_index import SpatialGrid


class Quadtree:
    """Thin wrapper around :class:`SpatialGrid` for future optimisation."""

    def __init__(self, cell_size: int) -> None:
        self._grid = SpatialGrid(cell_size)

    def insert(self, entity_id: int, pos: Tuple[int, int]) -> None:
        self._grid.insert(entity_id, pos)

    def remove(self, entity_id: int) -> None:
        self._grid.remove(entity_id)

    def query_radius(self, pos: Tuple[int, int], radius: int) -> List[int]:
        return self._grid.query_radius(pos, radius)


__all__ = ["Quadtree"]
