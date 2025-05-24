from __future__ import annotations

from typing import Any, Dict

from ...core.components.ai_state import AIState
from ...core.components.role import RoleComponent
from .behavior_tree import BehaviorTree, build_fallback_tree


class BehaviorTreeSystem:
    """Run behaviour trees for agents based on their role."""

    def __init__(
        self,
        world: Any,
        role_trees: Dict[str, BehaviorTree] | None = None,
        default_tree: BehaviorTree | None = None,
    ) -> None:
        self.world = world
        self.role_trees: Dict[str, BehaviorTree] = role_trees or {}
        self.default_tree = default_tree or build_fallback_tree()

    def register_tree(self, role: str, tree: BehaviorTree) -> None:
        self.role_trees[role] = tree

    def update(self, tick: int) -> None:
        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        out = getattr(self.world, "raw_actions_with_actor", None)
        if em is None or cm is None or out is None:
            return

        for entity_id in list(em.all_entities.keys()):
            if cm.get_component(entity_id, AIState) is None:
                continue
            role_comp = cm.get_component(entity_id, RoleComponent)
            role = role_comp.role_name if role_comp else None
            tree = self.role_trees.get(role, self.default_tree)
            action = tree.run(entity_id, self.world)
            if action:
                out.append((entity_id, action))


__all__ = ["BehaviorTreeSystem"]
