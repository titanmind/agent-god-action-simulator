# agent_world/systems/ai/actions.py
"""Utilities for parsing LLM-issued action strings."""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Deque, Optional, Union, List
import logging

logger = logging.getLogger(__name__)


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

@dataclass(slots=True)
class GenerateAbilityAction:
    """Request generation of a new ability."""
    actor: int
    description: str

@dataclass(slots=True)
class UseAbilityAction:
    """Use an existing ability."""
    actor: int
    ability_name: str
    target_id: Optional[int] = None

@dataclass(slots=True)
class PickupAction: 
    """Attempt to pick up an item."""
    actor: int
    item_id: int


Action = Union[
    MoveAction, AttackAction, LogAction, IdleAction, 
    GenerateAbilityAction, UseAbilityAction, PickupAction
]

_DIRECTION_MAP: dict[str, tuple[int, int]] = {
    "N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0),
}

def _parse_single_action_segment(actor: int, command_segment: str) -> Optional[Action]:
    """Parses a single command segment like "MOVE N" or "LOG message" """
    parts = command_segment.strip().split(maxsplit=1) 
    if not parts: return None
    cmd = parts[0].upper()
    arg_str = parts[1].strip() if len(parts) > 1 else ""
    logger.debug(
        "_parse_single_action_segment actor=%s cmd=%s arg_str=%s",
        actor,
        cmd,
        arg_str,
    )


    if cmd == "MOVE" and arg_str:
        delta = _DIRECTION_MAP.get(arg_str.upper())
        if delta is None: 
            logger.warning(
                "Invalid direction for MOVE: %s", arg_str
            )
            return None
        return MoveAction(actor=actor, dx=delta[0], dy=delta[1])
    if cmd == "ATTACK" and arg_str.isdigit():
        return AttackAction(actor=actor, target=int(arg_str))
    if cmd == "LOG": 
        return LogAction(actor=actor, message=arg_str) 
    if cmd == "IDLE" and not arg_str:
        return IdleAction(actor=actor)
    
    if cmd == "GENERATE_ABILITY" and arg_str:
        logger.debug(
            "Matched GENERATE_ABILITY for actor %s with desc %s",
            actor,
            arg_str,
        )
        return GenerateAbilityAction(actor=actor, description=arg_str)
        
    if cmd == "USE_ABILITY":
        ability_parts = arg_str.split(maxsplit=1)
        ability_name = ability_parts[0]
        target_id_str = ability_parts[1] if len(ability_parts) > 1 else None
        target_id = None
        if target_id_str and target_id_str.isdigit():
            target_id = int(target_id_str)
        elif target_id_str: 
            logger.warning(
                "Invalid target_id '%s' for USE_ABILITY.", target_id_str
            )
            return None 
        return UseAbilityAction(actor=actor, ability_name=ability_name, target_id=target_id)
    if cmd == "PICKUP" and arg_str.isdigit():
        return PickupAction(actor=actor, item_id=int(arg_str))

    logger.debug(
        "No match for cmd %s from segment %s", cmd, command_segment
    )
    return None # Return None if no command matched


def parse_action_string(actor: int, text: str) -> List[Action]:
    """
    Parses a full action string from the LLM.
    Can handle a "LOG ...\n<OTHER_ACTION> ..." sequence.
    Returns a list of actions.
    """
    actions: List[Action] = []
    raw_text = text.strip()
    
    logger.debug(
        "parse_action_string PRE-SPLIT actor=%s text=%s",
        actor,
        raw_text.replace(chr(10), " // "),
    )

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    if not lines:
        logger.debug(
            "No non-empty lines found for actor %s from text %s",
            actor,
            raw_text,
        )
        return actions

    first_action_text = lines[0]
    logger.debug(
        "Attempting to parse first_action_text %s for actor %s",
        first_action_text,
        actor,
    )
    first_action = _parse_single_action_segment(actor, first_action_text)

    if first_action:
        actions.append(first_action)
        if isinstance(first_action, LogAction) and len(lines) > 1:
            second_action_text = lines[1]
            logger.debug(
                "Attempting to parse second_action_text (after LOG) %s for actor %s",
                second_action_text,
                actor,
            )
            second_action = _parse_single_action_segment(actor, second_action_text)
            if second_action:
                actions.append(second_action)
            elif second_action_text:
                logger.warning(
                    "Second line '%s' after LOG did not parse into a valid action for actor %s",
                    second_action_text,
                    actor,
                )
    elif first_action_text:
        logger.warning(
            "Failed to parse primary action from: '%s' for actor %s",
            first_action_text,
            actor,
        )
            
    if not actions and raw_text:
        logger.warning(
            "Failed to parse any valid action from full text: '%s' for actor %s",
            raw_text,
            actor,
        )

    return actions


class ActionQueue:
    """Simple FIFO queue for parsed actions."""
    def __init__(self) -> None:
        self._queue: Deque[Action] = deque()

    def enqueue_raw(self, actor: int, text: str) -> None:
        """Parse ``text`` and enqueue the resulting action(s) if valid."""
        logger.debug(
            "ActionQueue.enqueue_raw PRE-PARSE actor=%s text=%s",
            actor,
            text[:100].replace(chr(10), " // "),
        )
        parsed_actions = parse_action_string(actor, text)
        logger.debug(
            "ActionQueue.enqueue_raw POST-PARSE actor=%s parsed_actions=%s",
            actor,
            parsed_actions,
        )

        if parsed_actions:
            for action in parsed_actions:
                self._queue.append(action)
                # Using a slightly more informative log for the actual enqueued action
                logger.info(
                    "ActionQueue.enqueue_raw: Actor %s enqueued %s(%s). Queue: %s",
                    actor,
                    type(action).__name__,
                    action,
                    len(self._queue),
                )
        else:
            # This log might be redundant if parse_action_string already logs failures, but good for explicit "nothing enqueued"
            logger.warning(
                "ActionQueue.enqueue_raw: No valid actions parsed or enqueued from '%s...' for actor %s",
                text[:60].replace(chr(10), " // "),
                actor,
            )


    def pop(self) -> Optional[Action]:
        if self._queue:
            return self._queue.popleft()
        return None

    def __len__(self) -> int:
        return len(self._queue)

__all__ = [
    "MoveAction", "AttackAction", "LogAction", "IdleAction", 
    "GenerateAbilityAction", "UseAbilityAction", "PickupAction", "Action",
    "ActionQueue", "parse_action_string",
]