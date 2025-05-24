from __future__ import annotations

from typing import Any, Optional

from agent_world.systems.ai.behavior_tree import (
    Action,
    BehaviorTree,
    Selector,
    fallback_explore_action,
)
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.combat.combat_system import CombatSystem


def _attack_adjacent(agent_id: int, world: Any) -> Optional[str]:
    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    if em is None or cm is None:
        return None
    my_pos = cm.get_component(agent_id, Position)
    if my_pos is None:
        return None
    for other_id in list(em.all_entities.keys()):
        if other_id == agent_id:
            continue
        other_pos = cm.get_component(other_id, Position)
        other_hp = cm.get_component(other_id, Health)
        if other_pos and other_hp and other_hp.cur > 0:
            if CombatSystem._in_melee_range(my_pos, other_pos):
                return f"USE_ABILITY MeleeStrike {other_id}"
    return None


def build_creature_tree() -> BehaviorTree:
    attack_node = Action(_attack_adjacent)
    wander_node = Action(fallback_explore_action)
    root = Selector([attack_node, wander_node])
    return BehaviorTree(root)


__all__ = ["build_creature_tree"]
