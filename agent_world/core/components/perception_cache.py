"""Component caching an entity's perception data for the current tick."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from agent_world.core.events import AbilityUseEvent


@dataclass(slots=True)
class PerceptionCache:
    """Stores visible entity IDs and the last tick they were updated."""

    visible: List[int] = field(default_factory=list)
    visible_ability_uses: list[AbilityUseEvent] = field(default_factory=list)
    last_tick: int = 0

