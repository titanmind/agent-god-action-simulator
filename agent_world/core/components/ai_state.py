"""Component representing the AI-related state for an entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class AIState:
    """Simple container for an entity's personality and current goals."""

    personality: str
    goals: List[str] = field(default_factory=list)
    pending_llm_prompt_id: str | None = None
    last_llm_action_tick: int = -1

