"""Entity management for the Agent World Simulator."""

from __future__ import annotations

from typing import Any, Dict


class EntityManager:
    """Simple entity manager maintaining entity/component mappings."""

    def __init__(self) -> None:
        self._next_id: int = 0
        # Mapping of entity_id -> component_name -> component_instance
        self._entity_components: Dict[int, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Creation / Destruction
    # ------------------------------------------------------------------
    def create_entity(self) -> int:
        """Create a new entity and return its unique ID."""

        self._next_id += 1
        entity_id = self._next_id
        self._entity_components[entity_id] = {}
        return entity_id

    def destroy_entity(self, entity_id: int) -> None:
        """Remove ``entity_id`` and all associated components."""

        self._entity_components.pop(entity_id, None)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def has_entity(self, entity_id: int) -> bool:
        return entity_id in self._entity_components

    def components(self, entity_id: int) -> Dict[str, Any]:
        return self._entity_components[entity_id]

    # Expose internal state for tests or debugging
    @property
    def all_entities(self) -> Dict[int, Dict[str, Any]]:
        return self._entity_components

