"""System updating entities' perception caches."""

from __future__ import annotations

from typing import List

from agent_world.core.world import World
from agent_world.core.components.position import Position
from agent_world.core.components.perception_cache import PerceptionCache
from .line_of_sight import has_line_of_sight


class PerceptionSystem:
    """Populate :class:`PerceptionCache` components each tick."""

    def __init__(self, world: World, view_radius: int = 5) -> None:
        self.world = world
        self.view_radius = view_radius

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def update(self, tick: int) -> None:
        """Refresh perception caches for all entities."""

        if (
            self.world.entity_manager is None
            or self.world.component_manager is None
            or self.world.spatial_index is None
        ):
            return

        em = self.world.entity_manager
        cm = self.world.component_manager
        spatial = self.world.spatial_index

        for entity_id in list(em.all_entities.keys()):
            cache = cm.get_component(entity_id, PerceptionCache)
            if cache is None:
                continue
            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue

            nearby = spatial.query_radius((pos.x, pos.y), self.view_radius)
            visible: List[int] = []
            for other_id in nearby:
                if other_id == entity_id:
                    continue
                other_pos = cm.get_component(other_id, Position)
                if other_pos is None:
                    continue
                if has_line_of_sight(pos, other_pos, self.view_radius):
                    visible.append(other_id)

            cache.visible = visible
            cache.last_tick = tick


__all__ = ["PerceptionSystem"]
