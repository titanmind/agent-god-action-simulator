"""Simple world container for core managers and tile map."""

from __future__ import annotations

from typing import Any, List, Tuple

from ..utils.asset_generation import noise


class World:
    """Lightweight holder for tile map and manager references."""

    def __init__(self, size: Tuple[int, int]):
        self.size: Tuple[int, int] = size
        width, height = size
        self.tile_map: List[List[Any]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

        # These managers will be populated during the bootstrapping phase.
        self.entity_manager = None
        self.component_manager = None
        self.systems_manager = None
        self.time_manager = None
        self.spatial_index = None

        # Pre-computed glyph/colour data for resource types
        self._resource_defs = {
            "ore": {"glyph": "O", "colour": "yellow"},
            "wood": {"glyph": "W", "colour": "green"},
            "herbs": {"glyph": "H", "colour": "magenta"},
        }

    # ------------------------------------------------------------------
    # Entity operations
    # ------------------------------------------------------------------
    def add_entity(self, entity_id: int) -> None:
        """Stub for adding an entity to the world."""
        if self.entity_manager is not None:
            self.entity_manager.create_entity(entity_id)  # type: ignore[attr-defined]

    def remove_entity(self, entity_id: int) -> None:
        """Stub for removing an entity from the world."""
        if self.entity_manager is not None:
            self.entity_manager.destroy_entity(entity_id)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # System operations
    # ------------------------------------------------------------------
    def register_system(self, system: Any) -> None:
        """Stub for registering a system."""
        if self.systems_manager is not None:
            self.systems_manager.register(system)  # type: ignore[attr-defined]

    def unregister_system(self, system: Any) -> None:
        """Stub for unregistering a system."""
        if self.systems_manager is not None:
            self.systems_manager.unregister(system)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Resource utilities
    # ------------------------------------------------------------------
    def spawn_resource(self, kind: str, x: int, y: int) -> None:
        """Place a resource node of ``kind`` at ``(x, y)`` if in bounds."""

        if kind not in self._resource_defs:
            raise ValueError(f"Unknown resource type: {kind}")
        if not (0 <= x < self.size[0] and 0 <= y < self.size[1]):
            return

        tile = {"kind": kind}
        tile.update(self._resource_defs[kind])
        self.tile_map[y][x] = tile

    def generate_resources(self, seed: int | None = None) -> None:
        """Populate ``tile_map`` with resource nodes using white-noise."""

        data = noise.white_noise(self.size[0], self.size[1], seed=seed)
        for y, row in enumerate(data):
            for x, value in enumerate(row):
                if value >= 0.98:
                    self.spawn_resource("ore", x, y)
                elif value >= 0.95:
                    self.spawn_resource("wood", x, y)
                elif value >= 0.9:
                    self.spawn_resource("herbs", x, y)
