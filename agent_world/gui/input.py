"""Handle basic input events and enqueue actions via :class:`ActionQueue`."""

from __future__ import annotations

from typing import Any, Dict

import pygame

from ..systems.ai.actions import ActionQueue, PLAYER_ID
from ..core.components.position import Position
from ..utils.asset_generation import sprite_gen
from ..utils import observer
from ..utils.cli import commands


def _screen_to_world(renderer: Any, pos: tuple[int, int]) -> tuple[int, int]:
    """Convert screen ``pos`` to integer world coordinates."""

    tile_w, tile_h = sprite_gen.SPRITE_SIZE
    x = int(pos[0] / (tile_w * getattr(renderer, "zoom", 1.0)) + renderer.center[0])
    y = int(pos[1] / (tile_h * getattr(renderer, "zoom", 1.0)) + renderer.center[1])
    return x, y


def _direction_to(dx: int, dy: int) -> str:
    """Return cardinal direction from ``dx``/``dy`` for MOVE actions."""

    if abs(dx) > abs(dy):
        return "E" if dx > 0 else "W"
    return "S" if dy > 0 else "N"


def handle_events(world: Any, renderer: Any, queue: ActionQueue, state: Dict[str, Any]) -> None:
    """Process ``pygame`` events and queue actions or hot-key commands."""

    cm = getattr(world, "component_manager", None)
    index = getattr(world, "spatial_index", None)
    tm = getattr(world, "time_manager", None)

    for ev in pygame.event.get():
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if cm is None or index is None:
                continue
            wx, wy = _screen_to_world(renderer, ev.pos)
            hits = index.query_radius((wx, wy), 0)
            if not hits:
                continue
            target = hits[0]
            ppos = cm.get_component(PLAYER_ID, Position)
            tpos = cm.get_component(target, Position)
            if ppos is None or tpos is None:
                continue
            if abs(tpos.x - ppos.x) + abs(tpos.y - ppos.y) <= 1:
                queue.enqueue_raw(PLAYER_ID, f"ATTACK {target}")
            else:
                dx = tpos.x - ppos.x
                dy = tpos.y - ppos.y
                queue.enqueue_raw(PLAYER_ID, f"MOVE {_direction_to(dx, dy)}")
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE:
                state["paused"] = not state.get("paused", False)
            elif ev.key == pygame.K_f:
                if tm is not None:
                    observer.install_tick_observer(tm)
                state["fps"] = observer.toggle_live_fps()
            elif ev.key == pygame.K_r:
                commands.reload_abilities(world)


__all__ = ["handle_events"]
