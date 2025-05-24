"""Track recent ability usage events for an entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from agent_world.core.events import AbilityUseEvent


@dataclass(slots=True)
class EventLog:
    """Component holding recently observed :class:`AbilityUseEvent`s."""

    recent: List[AbilityUseEvent] = field(default_factory=list)


__all__ = ["EventLog"]
