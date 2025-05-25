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
from agent_world.core.components.known_abilities import KnownAbilitiesComponent
from agent_world.systems.combat.combat_system import CombatSystem


def _direction_away(src: tuple[int, int], dst: tuple[int, int]) -> str:
    dx = src[0] - dst[0]
    dy = src[1] - dst[1]
    if abs(dx) > abs(dy):
        return "E" if dx > 0 else "W"
    if dy != 0:
        return "S" if dy > 0 else "N"
    return "N"


def _retreat_if_low_health(agent_id: int, world: Any) -> Optional[str]:
    cm = getattr(world, "component_manager", None)
    index = getattr(world, "spatial_index", None)
    if cm is None or index is None:
        return None
    hp = cm.get_component(agent_id, Health)
    pos = cm.get_component(agent_id, Position)
    if hp is None or pos is None or hp.max <= 0 or hp.cur / hp.max > 0.3:
        return None
    nearest_pos: Optional[Position] = None
    nearest_dist2: Optional[int] = None
    for other in index.query_radius((pos.x, pos.y), 3):
        if other == agent_id:
            continue
        o_pos = cm.get_component(other, Position)
        if o_pos is None:
            continue
        dist2 = (o_pos.x - pos.x) ** 2 + (o_pos.y - pos.y) ** 2
        if nearest_dist2 is None or dist2 < nearest_dist2:
            nearest_dist2 = dist2
            nearest_pos = o_pos
    if nearest_pos is None:
        return None
    direction = _direction_away((pos.x, pos.y), (nearest_pos.x, nearest_pos.y))
    return f"MOVE {direction}"


def _attack_best_target(agent_id: int, world: Any) -> Optional[str]:
    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    if em is None or cm is None:
        return None
    my_pos = cm.get_component(agent_id, Position)
    if my_pos is None:
        return None
    target_id: Optional[int] = None
    best_dist2: Optional[int] = None
    for other in list(em.all_entities.keys()):
        if other == agent_id:
            continue
        other_pos = cm.get_component(other, Position)
        other_hp = cm.get_component(other, Health)
        if other_pos and other_hp and other_hp.cur > 0:
            dist2 = (other_pos.x - my_pos.x) ** 2 + (other_pos.y - my_pos.y) ** 2
            if best_dist2 is None or dist2 < best_dist2:
                best_dist2 = dist2
                target_id = other
    if target_id is None:
        return None
    kab = cm.get_component(agent_id, KnownAbilitiesComponent)
    if kab and "MeleeStrike" in kab.known_class_names:
        return f"USE_ABILITY MeleeStrike {target_id}"
    if CombatSystem._in_melee_range(my_pos, cm.get_component(target_id, Position)):
        return f"ATTACK {target_id}"
    return None


def build_combat_tree() -> BehaviorTree:
    root = Selector([
        Action(_retreat_if_low_health),
        Action(_attack_best_target),
        Action(fallback_explore_action),
    ])
    return BehaviorTree(root)


__all__ = ["build_combat_tree"]
