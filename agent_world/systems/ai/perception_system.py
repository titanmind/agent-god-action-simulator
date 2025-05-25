"""Distribute ability use events to agents that can perceive them."""

from __future__ import annotations

from typing import Any, List

from ...core.components.perception_cache import PerceptionCache
from ...core.components.event_log import EventLog
from ...core.events import AbilityUseEvent
import agent_world.systems.ability.ability_system as ability_mod


class EventPerceptionSystem:
    """Deliver :class:`AbilityUseEvent`s to nearby agents."""

    def __init__(self, world: Any, event_queue: List[AbilityUseEvent] | None = None) -> None:
        self.world = world
        self.event_queue: List[AbilityUseEvent] = event_queue if event_queue is not None else getattr(
            ability_mod, "GLOBAL_ABILITY_EVENT_QUEUE", []
        )
        self._last_index = 0

    def update(self, tick: int) -> None:
        if not self.event_queue:
            return
        if self.world.entity_manager is None or self.world.component_manager is None:
            return

        em = self.world.entity_manager
        cm = self.world.component_manager
        new_events = self.event_queue[self._last_index :]
        self._last_index = len(self.event_queue)

        for event in new_events:
            relevant = {event.caster_id}
            if event.target_id is not None:
                relevant.add(event.target_id)
            for entity_id in list(em.all_entities.keys()):
                cache = cm.get_component(entity_id, PerceptionCache)
                if cache is None:
                    continue
                if not any(eid in cache.visible for eid in relevant):
                    continue
                log = cm.get_component(entity_id, EventLog)
                if log is None:
                    log = EventLog()
                    cm.add_component(entity_id, log)
                log.recent.append(event)
                # Track visible ability uses on the PerceptionCache itself
                cache.visible_ability_uses.append(event)


__all__ = ["EventPerceptionSystem"]
