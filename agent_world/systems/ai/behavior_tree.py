"""Minimal behavior tree utilities for simple agent fallbacks."""

from __future__ import annotations

from typing import Any, Callable, List, Optional


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
        """Execute the tree for ``agent_id``."""

        return self.root.run(agent_id, world)


def build_fallback_tree() -> BehaviorTree:
    """Return a simple Selector → Sequence → Action tree.

    The leaf action moves the agent north and is used when the LLM
    is busy and returns ``"<wait>"``.
    """

    def move_north(_: int, __: Any) -> str:
        return "MOVE N"

    action = Action(move_north)
    sequence = Sequence([action])
    root = Selector([sequence])
    return BehaviorTree(root)


__all__ = [
    "Node",
    "Action",
    "Sequence",
    "Selector",
    "BehaviorTree",
    "build_fallback_tree",
]
