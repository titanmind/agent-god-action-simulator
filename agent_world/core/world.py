"""Simple world container for core managers and tile map."""

from __future__ import annotations

from typing import List, Tuple, Any


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
