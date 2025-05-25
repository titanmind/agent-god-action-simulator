"""Track recent ability usage events for an entity."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from agent_world.core.events import AbilityUseEvent

# Maximum number of events retained in :class:`EventLog.recent`.
MAX_RECENT_EVENTS = 20


@dataclass(slots=True)
class EventLog:
    """Component holding recently observed :class:`AbilityUseEvent`s."""

    recent: Deque[AbilityUseEvent] = field(
        default_factory=lambda: deque(maxlen=MAX_RECENT_EVENTS)
    )

    def __post_init__(self) -> None:
        """Ensure ``recent`` is a deque with the correct ``maxlen``."""
        if not isinstance(self.recent, deque) or self.recent.maxlen != MAX_RECENT_EVENTS:
            self.recent = deque(self.recent, maxlen=MAX_RECENT_EVENTS)


__all__ = ["EventLog", "MAX_RECENT_EVENTS"]
