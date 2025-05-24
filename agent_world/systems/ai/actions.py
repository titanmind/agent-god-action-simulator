
"""Utilities for parsing LLM-issued action strings."""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Deque, Optional, Union, List # Added List

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

def _parse_single_action_segment(actor: int, command_segment: str) -> Optional[Action]:
    """Parses a single command segment like "MOVE N" or "LOG message" """
    parts = command_segment.strip().split(maxsplit=1)
    if not parts: return None
    cmd = parts[0].upper()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "MOVE" and arg:
        delta = _DIRECTION_MAP.get(arg.upper())
        if delta is None: return None
        return MoveAction(actor=actor, dx=delta[0], dy=delta[1])
    if cmd == "ATTACK" and arg.isdigit():
        return AttackAction(actor=actor, target=int(arg))
    if cmd == "LOG": # Allow LOG without message for simplicity, or LOG with message
        return LogAction(actor=actor, message=arg) # arg can be empty
    if cmd == "IDLE" and not arg: # IDLE should not have arguments
        return IdleAction(actor=actor)
    # Add other action parsing here (GENERATE_ABILITY, USE_ABILITY, PICKUP) when ready
    if cmd == "GENERATE_ABILITY" and arg:
        # Placeholder: For now, let's treat it like a LOG action of the request.
        # Actual GenerateAbilityAction would be different.
        return LogAction(actor=actor, message=f"REQUEST_GENERATE_ABILITY: {arg}")
    if cmd == "PICKUP" and arg.isdigit():
        # Placeholder:
        return LogAction(actor=actor, message=f"REQUEST_PICKUP: Item {arg}")

    return None


def parse_action_string(actor: int, text: str) -> List[Action]:
    """
    Parses a full action string from the LLM.
    Can handle a "LOG ... MOVE X" sequence by splitting it.
    Returns a list of actions (usually one, sometimes two if LOG+MOVE).
    """
    actions: List[Action] = []
    text = text.strip()

    # Heuristic for "LOG ... MOVE X"
    # Check if "LOG " is at the start and " MOVE " is present later
    log_prefix = "LOG "
    move_separator_options = [" MOVE N", " MOVE S", " MOVE E", " MOVE W"]
    
    parsed_complex = False
    if text.upper().startswith(log_prefix):
        for move_sep in move_separator_options:
            # Case-insensitive find for " MOVE <DIR>"
            # We need to find the start of " MOVE " to split correctly
            move_keyword_pos = text.upper().find(move_sep) # Find " MOVE N", " MOVE S", etc.
            
            if move_keyword_pos > len(log_prefix): # Ensure " MOVE " is after some log message
                log_content = text[len(log_prefix):move_keyword_pos].strip()
                move_command_full = text[move_keyword_pos:].strip() # "MOVE N"
                
                log_action = _parse_single_action_segment(actor, f"LOG {log_content}")
                move_action = _parse_single_action_segment(actor, move_command_full)
                
                if log_action: actions.append(log_action)
                if move_action: actions.append(move_action)
                
                if log_action and move_action: # Successfully parsed both
                    parsed_complex = True
                    break 
                else: # Reset if only one part parsed, fallback to single parse
                    actions.clear()
    
    if not parsed_complex:
        # Fallback to parsing the whole string as a single action
        single_action = _parse_single_action_segment(actor, text)
        if single_action:
            actions.append(single_action)
            
    if not actions and text: # If still no actions parsed but there was text, log the failure to parse
        print(f"[ActionParse] Failed to parse any valid action from: '{text}' for actor {actor}")

    return actions


class ActionQueue:
    """Simple FIFO queue for parsed actions."""
    def __init__(self) -> None:
        self._queue: Deque[Action] = deque()

    def enqueue_raw(self, actor: int, text: str) -> None:
        """Parse ``text`` and enqueue the resulting action(s) if valid."""
        parsed_actions = parse_action_string(actor, text)
        if parsed_actions:
            for action in parsed_actions:
                self._queue.append(action)
                print(f"[Tick ??] ActionQueue.enqueue_raw: Parsed '{text}' for actor {actor} into {action}. Queue size now: {len(self._queue)}")
        # else: # Optional: Log parsing failures (now handled in parse_action_string)
            # print(f"[Tick ??] ActionQueue.enqueue_raw: Failed to parse any action from '{text}' for actor {actor}.")


    def pop(self) -> Optional[Action]:
        if self._queue:
            return self._queue.popleft()
        return None

    def __len__(self) -> int:
        return len(self._queue)

__all__ = [
    "MoveAction", "AttackAction", "LogAction", "IdleAction", "Action",
    "ActionQueue", "parse_action_string", "PLAYER_ID", # Exposed parse_action_string
]