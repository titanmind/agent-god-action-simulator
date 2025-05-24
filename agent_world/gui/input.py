
"""Handle basic input events and enqueue actions via :class:`ActionQueue`."""

from __future__ import annotations

from typing import Any, Dict

import pygame

from ..systems.ai.actions import ActionQueue, PLAYER_ID
from ..core.components.position import Position
from ..utils.asset_generation import sprite_gen
from ..utils import observer
from ..utils.cli import commands # For reload_abilities


def _screen_to_world(renderer: Any, screen_pos: tuple[int, int]) -> tuple[int, int]:
    """Convert screen ``screen_pos`` to integer world coordinates."""
    if renderer.window is None: # Should not happen if GUI is active
        return 0,0

    tile_w, tile_h = sprite_gen.SPRITE_SIZE # Assuming this is base size before zoom
    
    zoom_level = getattr(renderer, "zoom", 1.0)
    if zoom_level == 0: zoom_level = 1.0

    # Screen center in screen coordinates
    screen_center_x = renderer.window.size[0] / 2
    screen_center_y = renderer.window.size[1] / 2

    # World coordinates of camera center
    camera_world_x = renderer.center[0]
    camera_world_y = renderer.center[1]

    # Transform screen_pos relative to screen center, then scale by zoom, then add camera world pos
    world_x = camera_world_x + (screen_pos[0] - screen_center_x) / (tile_w * zoom_level)
    world_y = camera_world_y + (screen_pos[1] - screen_center_y) / (tile_h * zoom_level)
    
    return int(round(world_x)), int(round(world_y))


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

    # Camera pan speed
    pan_speed = 5.0 / renderer.zoom # Pan faster when zoomed out, slower when zoomed in

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            state["running"] = False
            return

        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1: # Left click
                if cm is None or index is None:
                    continue
                wx, wy = _screen_to_world(renderer, ev.pos)
                hits = index.query_radius((wx, wy), 0) # Query point, radius 0
                
                # print(f"Mouse click at screen {ev.pos} -> world ({wx},{wy}). Hits: {hits}") # Debugging
                
                if not hits: # If clicked empty space, maybe move player there eventually
                    # For now, only interact with entities
                    # Or, if you want to move to location:
                    # ppos = cm.get_component(PLAYER_ID, Position)
                    # if ppos:
                    #     dx_world, dy_world = wx - ppos.x, wy - ppos.y
                    #     if dx_world !=0 or dy_world !=0:
                    #          queue.enqueue_raw(PLAYER_ID, f"MOVE_TO {wx} {wy}") # Requires new action type
                    continue

                target_id = hits[0] # Simplistic: take the first hit
                ppos = cm.get_component(PLAYER_ID, Position)
                tpos = cm.get_component(target_id, Position)

                if ppos is None or tpos is None:
                    continue
                
                # Manhattan distance for melee range check (example)
                if abs(tpos.x - ppos.x) + abs(tpos.y - ppos.y) <= 1:
                    queue.enqueue_raw(PLAYER_ID, f"ATTACK {target_id}")
                else: # If not in melee, move towards (example of simple move)
                    # This is a very basic "move one step towards"
                    dx_world = tpos.x - ppos.x
                    dy_world = tpos.y - ppos.y
                    if dx_world != 0 or dy_world !=0: # Check if not already at target pos
                        direction_str = _direction_to(dx_world, dy_world)
                        queue.enqueue_raw(PLAYER_ID, f"MOVE {direction_str}")
            
        elif ev.type == pygame.MOUSEWHEEL: # Zoom
            scroll_amount = ev.y
            zoom_factor = 1.1 if scroll_amount > 0 else 1 / 1.1
            renderer.zoom *= zoom_factor
            renderer.zoom = max(0.1, min(renderer.zoom, 5.0)) # Clamp zoom

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE:
                state["paused"] = not state.get("paused", False)
                print(f"Simulation {'paused' if state['paused'] else 'resumed'}.")
            elif ev.key == pygame.K_f:
                if tm is not None:
                    observer.install_tick_observer(tm)
                # toggle_live_fps directly prints and returns new state
                fps_enabled_now = observer.toggle_live_fps()
                state["fps_enabled"] = fps_enabled_now # Update state for other parts of app
                world.fps_enabled = fps_enabled_now # Also update world's view if it uses it
            elif ev.key == pygame.K_r:
                commands.reload_abilities(world)
            
            # Camera pan keys
            elif ev.key == pygame.K_LEFT or ev.key == pygame.K_a:
                renderer.center[0] -= pan_speed
            elif ev.key == pygame.K_RIGHT or ev.key == pygame.K_d:
                renderer.center[0] += pan_speed
            elif ev.key == pygame.K_UP or ev.key == pygame.K_w:
                renderer.center[1] -= pan_speed
            elif ev.key == pygame.K_DOWN or ev.key == pygame.K_s:
                renderer.center[1] += pan_speed
            
            elif ev.key == pygame.K_ESCAPE: # Allow Esc to quit
                state["running"] = False
                return

    # Continuous pan if keys are held (alternative to discrete keydown events)
    # keys_pressed = pygame.key.get_pressed()
    # if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
    #     renderer.center[0] -= pan_speed * (1/60.0) # Assuming 60fps for smooth pan
    # if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
    #     renderer.center[0] += pan_speed * (1/60.0)
    # if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
    #     renderer.center[1] -= pan_speed * (1/60.0)
    # if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
    #     renderer.center[1] += pan_speed * (1/60.0)

__all__ = ["handle_events"]