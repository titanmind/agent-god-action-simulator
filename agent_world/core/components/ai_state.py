
"""Component representing the AI-related state for an entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional # Added Optional

@dataclass(slots=True)
class AIState:
    """Simple container for an entity's personality and current goals."""

    personality: str
    goals: List[str] = field(default_factory=list)
    pending_llm_prompt_id: str | None = None
    last_llm_action_tick: int = -1
    last_bt_direction_index: int = 0 # Index for cycling N, E, S, W
    last_bt_move_failed: bool = False # Flag if last BT move resulted in no actual movement (e.g. collision)
    needs_immediate_rethink: bool = False
    last_error: str | None = None
