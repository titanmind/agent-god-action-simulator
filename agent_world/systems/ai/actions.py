"""Utilities for parsing LLM-issued action strings."""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Deque, Optional, Union


# ID used by the GUI input handler for the local player controller
PLAYER_ID = 0


# ------------------------------------------------------------------
# Action dataclasses
# ------------------------------------------------------------------
@dataclass(slots=True)
class MoveAction:
    """Move the actor by a delta per tick."""
    actor: int
    dx: int
    dy: int

@dataclass(slots=True)
class AttackAction:
    """Attack a target entity."""
    actor: int
    target: int

@dataclass(slots=True)
class LogAction:
    """Log a message to the console."""
    actor: int
    message: str

@dataclass(slots=True)
class IdleAction:
    """No-op action used for a single tick."""
    actor: int

Action = Union[MoveAction, AttackAction, LogAction, IdleAction]

_DIRECTION_MAP: dict[str, tuple[int, int]] = {
    "N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0),
}

def parse_action(actor: int, text: str) -> Optional[Action]:
    parts = text.strip().split(maxsplit=1)
    if not parts: return None
    cmd = parts[0].upper()
    arg = parts[1] if len(parts) > 1 else ""
    if cmd == "MOVE" and arg:
        delta = _DIRECTION_MAP.get(arg.upper())
        if delta is None: return None
        return MoveAction(actor=actor, dx=delta[0], dy=delta[1])
    if cmd == "ATTACK" and arg.isdigit():
        return AttackAction(actor=actor, target=int(arg))
    if cmd == "LOG" and arg:
        return LogAction(actor=actor, message=arg)
    if cmd == "IDLE" and not arg:
        return IdleAction(actor=actor)
    return None

class ActionQueue:
    """Simple FIFO queue for parsed actions."""
    def __init__(self) -> None:
        self._queue: Deque[Action] = deque()

    def enqueue_raw(self, actor: int, text: str) -> None:
        """Parse ``text`` and enqueue the resulting action if valid."""
        action = parse_action(actor, text)
        if action is not None:
            self._queue.append(action)
            # --- LOGGING: Action Enqueued ---
            tm = getattr(getattr(action, '__self__', {}), 'world', {}).get('time_manager', None) # Attempt to get tick
            current_tick = tm.tick_counter if tm and hasattr(tm, 'tick_counter') else "N/A_in_enqueue"
            # Simplified tick fetching for this log, might not always work if world context isn't easily available here
            # A better way would be to pass tick to enqueue_raw if needed for logging.
            print(f"[Tick ??] ActionQueue.enqueue_raw: Parsed '{text}' for actor {actor} into {action}. Queue size now: {len(self._queue)}")
            # --- END LOGGING ---
        # else: # Optional: log parsing failures
            # print(f"[Tick ??] ActionQueue.enqueue_raw: Failed to parse action '{text}' for actor {actor}.")


    def pop(self) -> Optional[Action]:
        if self._queue:
            return self._queue.popleft()
        return None

    def __len__(self) -> int:
        return len(self._queue)

__all__ = [
    "MoveAction", "AttackAction", "LogAction", "IdleAction", "Action", 
    "ActionQueue", "parse_action", "PLAYER_ID",
]