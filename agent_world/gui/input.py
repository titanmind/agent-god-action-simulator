"""Handle basic input events and enqueue actions via :class:`ActionQueue`."""

from __future__ import annotations
from typing import Any, Dict
import pygame

from ..systems.ai.actions import ActionQueue, PLAYER_ID
from ..core.components.position import Position
from ..utils import observer
from ..utils.cli import commands 

def _direction_to(dx: int, dy: int) -> str:
    """Return cardinal direction from ``dx``/``dy`` for MOVE actions."""
    if abs(dx) > abs(dy): return "E" if dx > 0 else "W"
    return "S" if dy > 0 else "N"

def handle_events(world: Any, renderer: Any, queue: ActionQueue, state: Dict[str, Any]) -> None:
    """Process ``pygame`` events and queue actions or hot-key commands."""
    cm = getattr(world, "component_manager", None)
    index = getattr(world, "spatial_index", None)
    tm = getattr(world, "time_manager", None)

    # Pan speed in screen pixels per key event
    pan_speed_pixels = 20.0  # <<<<<<< Pan speed is now in screen pixels

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            state["running"] = False
            return

        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1: 
                # Placeholder for click interaction
                # if cm and index and hasattr(renderer, 'world_to_screen'):
                #     # Need screen_to_world for this
                #     # wx, wy = renderer.screen_to_world(ev.pos)
                #     # ... then query spatial index at wx, wy ...
                pass
            
        elif ev.type == pygame.MOUSEWHEEL: 
            scroll_amount = ev.y
            factor = 1.1 if scroll_amount > 0 else (1 / 1.1)
            renderer.adjust_zoom(factor)

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE:
                state["paused"] = not state.get("paused", False)
                print(f"Simulation {'paused' if state['paused'] else 'resumed'}.")
            elif ev.key == pygame.K_f:
                if tm: observer.install_tick_observer(tm)
                fps_enabled_now = observer.toggle_live_fps()
                state["fps_enabled"] = fps_enabled_now 
                world.fps_enabled = fps_enabled_now 
            elif ev.key == pygame.K_r:
                commands.reload_abilities(world)
            
            elif ev.key == pygame.K_LEFT or ev.key == pygame.K_a:
                renderer.pan_camera(-pan_speed_pixels, 0) # <<<<<<< Pass screen pixel delta
            elif ev.key == pygame.K_RIGHT or ev.key == pygame.K_d:
                renderer.pan_camera(pan_speed_pixels, 0)  # <<<<<<< Pass screen pixel delta
            elif ev.key == pygame.K_UP or ev.key == pygame.K_w:
                renderer.pan_camera(0, -pan_speed_pixels) # <<<<<<< Pass screen pixel delta
            elif ev.key == pygame.K_DOWN or ev.key == pygame.K_s:
                renderer.pan_camera(0, pan_speed_pixels)  # <<<<<<< Pass screen pixel delta
            
            elif ev.key == pygame.K_ESCAPE: 
                state["running"] = False
                return
__all__ = ["handle_events"]