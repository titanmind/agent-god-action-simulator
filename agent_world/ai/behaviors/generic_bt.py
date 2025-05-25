from __future__ import annotations

from typing import Any, Optional

from ...systems.ai.behavior_tree import (
    Action,
    BehaviorTree,
    Selector,
    fallback_explore_action,
)
from ...core.components.position import Position
from ...core.components.health import Health
from ...systems.interaction.pickup import Tag


def _nearest_resource(world: Any, pos: tuple[int, int]) -> tuple[Optional[tuple[int, int]], Optional[str]]:
    tile_map = getattr(world, "tile_map", None)
    if not tile_map:
        return None, None
    best_pos: Optional[tuple[int, int]] = None
    best_kind: Optional[str] = None
    best_dist2: Optional[int] = None
    for y, row in enumerate(tile_map):
        for x, tile in enumerate(row):
            if tile and "kind" in tile:
                dist2 = (x - pos[0]) ** 2 + (y - pos[1]) ** 2
                if best_dist2 is None or dist2 < best_dist2:
                    best_dist2 = dist2
                    best_pos = (x, y)
                    best_kind = tile["kind"]
    return best_pos, best_kind


def _direction_towards(src: tuple[int, int], dst: tuple[int, int]) -> str:
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    if abs(dx) > abs(dy):
        return "E" if dx > 0 else "W"
    if dy != 0:
        return "S" if dy > 0 else "N"
    return "N"


def _direction_away(src: tuple[int, int], dst: tuple[int, int]) -> str:
    dx = src[0] - dst[0]
    dy = src[1] - dst[1]
    if abs(dx) > abs(dy):
        return "E" if dx > 0 else "W"
    if dy != 0:
        return "S" if dy > 0 else "N"
    return "N"


def _gather_resource_action(agent_id: int, world: Any) -> Optional[str]:
    cm = getattr(world, "component_manager", None)
    if cm is None:
        return None
    pos = cm.get_component(agent_id, Position)
    if pos is None:
        return None
    tile_map = getattr(world, "tile_map", None)
    if tile_map:
        tile = tile_map[pos.y][pos.x]
        if tile and "kind" in tile:
            return f"HARVEST {tile['kind']}"
    target, _kind = _nearest_resource(world, (pos.x, pos.y))
    if target is None:
        return None
    direction = _direction_towards((pos.x, pos.y), target)
    return f"MOVE {direction}"


def _flee_low_health_action(agent_id: int, world: Any, threshold: float = 0.3, radius: int = 3) -> Optional[str]:
    cm = getattr(world, "component_manager", None)
    index = getattr(world, "spatial_index", None)
    if cm is None or index is None:
        return None
    hp = cm.get_component(agent_id, Health)
    pos = cm.get_component(agent_id, Position)
    if hp is None or pos is None or hp.max <= 0 or hp.cur / hp.max > threshold:
        return None
    nearest_pos: Optional[Position] = None
    nearest_dist2: Optional[int] = None
    for other in index.query_radius((pos.x, pos.y), radius):
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


def _item_interaction_action(agent_id: int, world: Any, search_radius: int = 5) -> Optional[str]:
    cm = getattr(world, "component_manager", None)
    index = getattr(world, "spatial_index", None)
    if cm is None or index is None:
        return None
    pos = cm.get_component(agent_id, Position)
    if pos is None:
        return None
    for other in index.query_radius((pos.x, pos.y), 0):
        if other == agent_id:
            continue
        tag = cm.get_component(other, Tag)
        if tag and tag.name == "item":
            return f"PICKUP {other}"
    nearest: Optional[Position] = None
    best_dist2: Optional[int] = None
    for other in index.query_radius((pos.x, pos.y), search_radius):
        if other == agent_id:
            continue
        tag = cm.get_component(other, Tag)
        if tag and tag.name == "item":
            o_pos = cm.get_component(other, Position)
            if o_pos is None:
                continue
            dist2 = (o_pos.x - pos.x) ** 2 + (o_pos.y - pos.y) ** 2
            if best_dist2 is None or dist2 < best_dist2:
                best_dist2 = dist2
                nearest = o_pos
    if nearest is None:
        return None
    direction = _direction_towards((pos.x, pos.y), (nearest.x, nearest.y))
    return f"MOVE {direction}"


def build_resource_gather_tree() -> BehaviorTree:
    root = Selector([
        Action(_gather_resource_action),
        Action(fallback_explore_action),
    ])
    return BehaviorTree(root)


def build_flee_low_health_tree() -> BehaviorTree:
    root = Selector([
        Action(_flee_low_health_action),
        Action(fallback_explore_action),
    ])
    return BehaviorTree(root)


def build_item_interaction_tree() -> BehaviorTree:
    root = Selector([
        Action(_item_interaction_action),
        Action(fallback_explore_action),
    ])
    return BehaviorTree(root)


__all__ = [
    "build_resource_gather_tree",
    "build_flee_low_health_tree",
    "build_item_interaction_tree",
]
