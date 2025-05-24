"""Utilities for parsing LLM-issued action strings."""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Deque, Optional, Union


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


Action = Union[MoveAction, AttackAction]

# Map simple cardinal directions to deltas
_DIRECTION_MAP: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}


# ------------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------------

def parse_action(actor: int, text: str) -> Optional[Action]:
    """Return an :class:`Action` parsed from ``text``.

    The parser is intentionally strict: invalid strings return ``None`` so that
    erroneous LLM output is safely ignored.
    """

    parts = text.strip().split()
    if not parts:
        return None

    cmd = parts[0].upper()
    if cmd == "MOVE" and len(parts) == 2:
        direction = parts[1].upper()
        delta = _DIRECTION_MAP.get(direction)
        if delta is None:
            return None
        dx, dy = delta
        return MoveAction(actor=actor, dx=dx, dy=dy)

    if cmd == "ATTACK" and len(parts) == 2 and parts[1].isdigit():
        return AttackAction(actor=actor, target=int(parts[1]))

    return None


# ------------------------------------------------------------------
# ActionQueue utility
# ------------------------------------------------------------------
class ActionQueue:
    """Simple FIFO queue for parsed actions."""

    def __init__(self) -> None:
        self._queue: Deque[Action] = deque()

    def enqueue_raw(self, actor: int, text: str) -> None:
        """Parse ``text`` and enqueue the resulting action if valid."""

        action = parse_action(actor, text)
        if action is not None:
            self._queue.append(action)

    def pop(self) -> Optional[Action]:
        """Retrieve the next parsed action if available."""

        if self._queue:
            return self._queue.popleft()
        return None

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._queue)


__all__ = [
    "MoveAction",
    "AttackAction",
    "Action",
    "ActionQueue",
    "parse_action",
]
