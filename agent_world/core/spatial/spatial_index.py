from __future__ import annotations

from typing import Dict, List, Set, Tuple


class SpatialGrid:
    """Simple grid-based spatial index."""

    def __init__(self, cell_size: int) -> None:
        if cell_size <= 0:
            raise ValueError("cell_size must be positive")
        self.cell_size = cell_size
        self._cells: Dict[Tuple[int, int], Set[int]] = {}
        self._entity_pos: Dict[int, Tuple[int, int]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _cell_coords(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """Return integer cell coordinates for ``pos``."""
        x, y = pos
        return (x // self.cell_size, y // self.cell_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def insert(self, entity_id: int, pos: Tuple[int, int]) -> None:
        """Insert ``entity_id`` at ``pos``."""
        cell = self._cell_coords(pos)
        self._cells.setdefault(cell, set()).add(entity_id)
        self._entity_pos[entity_id] = pos

    def insert_many(self, items: List[Tuple[int, Tuple[int, int]]]) -> None:
        """Insert multiple ``(entity_id, pos)`` pairs in one batch."""
        cell_map: Dict[Tuple[int, int], List[int]] = {}
        for ent, pos in items:
            cell = self._cell_coords(pos)
            cell_map.setdefault(cell, []).append(ent)
            self._entity_pos[ent] = pos
        for cell, ents in cell_map.items():
            self._cells.setdefault(cell, set()).update(ents)

    def remove(self, entity_id: int) -> None:
        """Remove ``entity_id`` from the index."""
        pos = self._entity_pos.pop(entity_id, None)
        if pos is None:
            return
        cell = self._cell_coords(pos)
        entities = self._cells.get(cell)
        if entities is not None:
            entities.discard(entity_id)
            if not entities:
                self._cells.pop(cell, None)

    def query_radius(self, pos: Tuple[int, int], radius: int) -> List[int]:
        """Return all entity IDs within ``radius`` of ``pos``."""
        cx_min = (pos[0] - radius) // self.cell_size
        cx_max = (pos[0] + radius) // self.cell_size
        cy_min = (pos[1] - radius) // self.cell_size
        cy_max = (pos[1] + radius) // self.cell_size
        r2 = radius * radius
        results: List[int] = []
        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                cell_entities = self._cells.get((cx, cy))
                if not cell_entities:
                    continue
                for ent in cell_entities:
                    ex, ey = self._entity_pos[ent]
                    dx = ex - pos[0]
                    dy = ey - pos[1]
                    if dx * dx + dy * dy <= r2:
                        results.append(ent)
        return results


__all__ = ["SpatialGrid"]
