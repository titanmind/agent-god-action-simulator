
"""Minimal behavior tree utilities for simple agent fallbacks."""

from __future__ import annotations

from typing import Any, Callable, List, Optional
import logging
# No longer need Position from here directly for this simplified BT
from ...core.components.ai_state import AIState 

# Order of exploration for Behavior Tree
BT_EXPLORE_DIRECTIONS = ["N", "E", "S", "W"] # Cycle: N, E, S, W

logger = logging.getLogger(__name__)

class Node:
    """Base behavior tree node."""
    def run(self, agent_id: int, world: Any) -> Optional[str]:
        raise NotImplementedError

class Action(Node):
    """Execute ``func`` and return its result as the node's output."""
    def __init__(self, func: Callable[[int, Any], Optional[str]]) -> None:
        self.func = func

    def run(self, agent_id: int, world: Any) -> Optional[str]:
        return self.func(agent_id, world)

class Sequence(Node):
    """Run children in order until one fails (returns ``None``)."""
    def __init__(self, children: List[Node]) -> None:
        self.children = children

    def run(self, agent_id: int, world: Any) -> Optional[str]:
        result: Optional[str] = None
        for child in self.children:
            result = child.run(agent_id, world)
            if result is None:
                return None
        return result

class Selector(Node):
    """Run children until one succeeds (returns non-``None``)."""
    def __init__(self, children: List[Node]) -> None:
        self.children = children

    def run(self, agent_id: int, world: Any) -> Optional[str]:
        for child in self.children:
            result = child.run(agent_id, world)
            if result is not None:
                return result
        return None

class BehaviorTree:
    """Container for a tree with a single ``root`` node."""
    def __init__(self, root: Node) -> None:
        self.root = root

    def run(self, agent_id: int, world: Any) -> Optional[str]:
        return self.root.run(agent_id, world)


def fallback_explore_action(agent_id: int, world: Any) -> Optional[str]:
    """
    Fallback action for exploration. Cycles through N, E, S, W.
    The index is incremented *each time this is called for an agent*,
    meaning it will try a new direction on the next BT fallback.
    """
    if world.component_manager is None:
        return "IDLE" 

    ai_state = world.component_manager.get_component(agent_id, AIState)
    if ai_state is None:
        # This should ideally not happen for NPCs that are supposed to have AIState
        # If it does, we'll just pick 'N' to avoid errors, but it's a sign of setup issue.
        logger.warning("[BT] Agent %s missing AIState, defaulting BT to MOVE N.", agent_id)
        return "MOVE N"

    # Get current direction based on index
    direction = BT_EXPLORE_DIRECTIONS[ai_state.last_bt_direction_index]
    
    # Increment index for the *next* time this function is called for this agent
    ai_state.last_bt_direction_index = (ai_state.last_bt_direction_index + 1) % len(BT_EXPLORE_DIRECTIONS)
    
    return f"MOVE {direction}"


def build_fallback_tree() -> BehaviorTree:
    """
    Return a simple Selector -> Sequence -> Action tree.
    The leaf action cycles through MOVE N, E, S, W.
    """
    action_node = Action(fallback_explore_action)
    sequence = Sequence([action_node]) 
    root = Selector([sequence])       
    return BehaviorTree(root)


__all__ = [
    "Node",
    "Action",
    "Sequence",
    "Selector",
    "BehaviorTree",
    "build_fallback_tree",
    "fallback_explore_action"
]