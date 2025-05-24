
# agent_world/gui/renderer.py
"""Renderer for drawing entities to a :class:`Window`."""

from __future__ import annotations
from typing import Any
import math # For floor/ceil

from ..core.components.position import Position
from ..utils.asset_generation import sprite_gen
from ..utils import observer
from .window import Window
import pygame

# Define colors for tiles
TILE_COLOR_MAP = {
    "default": (70, 70, 70),    # Default empty ground
    "ore": (200, 180, 50),      # Yellowish for ore
    "wood": (100, 150, 50),     # Greenish for wood
    "herbs": (180, 100, 200),   # Purplish for herbs
    "obstacle": (40, 40, 40),   # Dark grey for obstacles
}
DEFAULT_TILE_GLYPH_COLOR = (200, 200, 200)

class Renderer:
    """Minimal renderer dispatching drawing to a :class:`Window`."""

    def __init__(self, window: Window | None = None) -> None:
        self.window = window if window is not None else Window()
        self.camera_world_x: float = 0.0
        self.camera_world_y: float = 0.0
        self.zoom: float = 16.0  # Pixels per world unit. Start more zoomed in.
        self.min_zoom = 4.0
        self.max_zoom = 64.0
        self.debug_font = pygame.font.SysFont(None, 18)
        if self.window and not pygame.font.get_init(): # Ensure font module is init
            pygame.font.init()
        try:
            self.tile_font = pygame.font.SysFont(None, int(self.zoom * 0.6)) # Dynamic font for tiles
        except Exception:
             self.tile_font = pygame.font.Font(None, 12) # Fallback

    def _update_tile_font_size(self):
        try:
            # Ensure font size is at least 1
            font_size = max(1, int(self.zoom * 0.5)) 
            self.tile_font = pygame.font.SysFont(None, font_size)
        except Exception:
            self.tile_font = pygame.font.Font(None, max(1, int(self.zoom * 0.5)))


    def set_camera_center(self, world_x: float, world_y: float):
        self.camera_world_x = world_x
        self.camera_world_y = world_y

    def adjust_zoom(self, factor: float):
        old_zoom = self.zoom
        mouse_world_x_before, mouse_world_y_before = self.screen_to_world_coords(pygame.mouse.get_pos())

        self.zoom *= factor
        self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom))
        self._update_tile_font_size()

        # Pan camera to keep mouse position fixed in world space after zoom
        if abs(old_zoom - self.zoom) > 0.001: # If zoom actually changed
            mouse_world_x_after, mouse_world_y_after = self.screen_to_world_coords(pygame.mouse.get_pos())
            self.camera_world_x += (mouse_world_x_before - mouse_world_x_after)
            self.camera_world_y += (mouse_world_y_before - mouse_world_y_after)


    def pan_camera(self, dx_screen: float, dy_screen: float):
        # Pan amount in screen pixels, convert to world units based on current zoom
        self.camera_world_x -= dx_screen / self.zoom
        self.camera_world_y -= dy_screen / self.zoom


    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        if not self.window: return 0, 0
        screen_center_px_x = self.window.size[0] / 2
        screen_center_px_y = self.window.size[1] / 2
        dx_world = world_x - self.camera_world_x
        dy_world = world_y - self.camera_world_y
        dx_pixels = dx_world * self.zoom
        dy_pixels = dy_world * self.zoom
        screen_x = screen_center_px_x + dx_pixels
        screen_y = screen_center_px_y + dy_pixels
        return int(screen_x), int(screen_y)

    def screen_to_world_coords(self, screen_pos: tuple[int, int]) -> tuple[float, float]:
        if not self.window: return 0.0, 0.0
        screen_x, screen_y = screen_pos
        screen_center_px_x = self.window.size[0] / 2
        screen_center_px_y = self.window.size[1] / 2

        # Delta from screen center in pixels
        dx_pixels = screen_x - screen_center_px_x
        dy_pixels = screen_y - screen_center_px_y

        # Convert pixel delta to world delta
        dx_world = dx_pixels / self.zoom
        dy_world = dy_pixels / self.zoom
        
        world_x = self.camera_world_x + dx_world
        world_y = self.camera_world_y + dy_world
        return world_x, world_y

    def _render_tiles(self, world: Any):
        if not self.window or not hasattr(world, 'tile_map') or not hasattr(world, 'size'):
            return

        tile_map = world.tile_map
        world_width, world_height = world.size
        
        # Calculate visible world range
        screen_w_world = self.window.size[0] / self.zoom
        screen_h_world = self.window.size[1] / self.zoom

        min_vis_wx = math.floor(self.camera_world_x - screen_w_world / 2) -1 # Add buffer for partial tiles
        max_vis_wx = math.ceil(self.camera_world_x + screen_w_world / 2) +1
        min_vis_wy = math.floor(self.camera_world_y - screen_h_world / 2) -1
        max_vis_wy = math.ceil(self.camera_world_y + screen_h_world / 2) +1

        tile_screen_size = int(self.zoom) # Each tile is 1x1 world unit

        # For pathfinding obstacles
        from ..systems.movement.pathfinding import OBSTACLES as pathfinding_obstacles

        for wy in range(min_vis_wy, max_vis_wy + 1):
            if not (0 <= wy < world_height): continue
            for wx in range(min_vis_wx, max_vis_wx + 1):
                if not (0 <= wx < world_width): continue

                tile_data = tile_map[wy][wx] # tile_map is [y][x]
                screen_x, screen_y = self.world_to_screen(float(wx), float(wy))

                color = TILE_COLOR_MAP["default"]
                glyph = None # By default, no glyph for empty ground

                if (wx, wy) in pathfinding_obstacles: # Check if it's a pathfinding obstacle
                    color = TILE_COLOR_MAP["obstacle"]
                    glyph = "#" 
                elif tile_data and isinstance(tile_data, dict):
                    kind = tile_data.get("kind")
                    color = TILE_COLOR_MAP.get(kind, color)
                    glyph = tile_data.get("glyph")
                
                # Draw tile background
                # Pygame rect: (left, top, width, height)
                pygame.draw.rect(self.window._surface, color, (screen_x, screen_y, tile_screen_size, tile_screen_size))
                
                # Draw glyph if any
                if glyph and self.zoom > 8: # Only draw glyphs if reasonably zoomed in
                    text_surf = self.tile_font.render(str(glyph), True, DEFAULT_TILE_GLYPH_COLOR)
                    text_rect = text_surf.get_rect(center=(screen_x + tile_screen_size // 2, screen_y + tile_screen_size // 2))
                    self.window._surface.blit(text_surf, text_rect)
                
                # Optional: Draw grid lines for debugging zoom/coords
                # if self.zoom > 15:
                #    pygame.draw.rect(self.window._surface, (50,50,50), (screen_x, screen_y, tile_screen_size, tile_screen_size), 1)


    def update(self, world: Any) -> None:
        tm = getattr(world, "time_manager", None)
        current_tick = tm.tick_counter if tm else "N/A"

        if self.window is None or not hasattr(self.window, '_surface'):
            return

        # 1. Render Tiles (background)
        self._render_tiles(world)

        # 2. Render Entities
        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None:
            return

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue

            try:
                # Scale sprite size based on zoom, but keep aspect ratio
                # Let's assume get_sprite always returns 32x32 base image
                base_sprite_pil = sprite_gen.get_sprite(entity_id)
                
                # Calculate sprite screen size based on zoom (e.g. 1 world unit for sprite)
                # For simplicity, let's say entity occupies 1x1 world unit.
                sprite_screen_width = int(self.zoom) 
                sprite_screen_height = int(self.zoom)

                # Use a cached pygame surface if possible, and scale it
                # (This part is tricky with PIL images directly)
                # For now, let Window handle PIL to Surface conversion and blit.
                # Scaling should ideally happen on the pygame.Surface for performance.
                # The `window.draw_sprite` doesn't scale yet.
                # Let's modify draw_sprite to accept target size.
                
                screen_x_blit, screen_y_blit = self.world_to_screen(float(pos.x), float(pos.y))
                
                # For now, window.draw_sprite will draw the PIL image at its native size
                # We need to adjust its blitting logic or scale here.
                # A simple way: if window.draw_sprite can take a target_size
                # self.window.draw_sprite(entity_id, screen_x_blit, screen_y_blit, base_sprite_pil, target_size=(sprite_screen_width, sprite_screen_height))
                
                # For now, let's just blit it, assuming zoom factor means sprite size.
                # This assumes the sprite's "hotspot" (world pos) is its top-left.
                # We can adjust if it should be center.
                
                # Modify draw_sprite to handle scaling or scale here (less efficient)
                # This simple blit won't scale the sprite with zoom.
                # self.window.draw_sprite(entity_id, screen_x_blit, screen_y_blit, base_sprite_pil)

                # Let's try asking the window to draw a scaled version.
                # This requires changing window.draw_sprite interface
                self.window.draw_sprite_scaled(entity_id, screen_x_blit, screen_y_blit, base_sprite_pil, 
                                               (sprite_screen_width, sprite_screen_height))


            except Exception as e:
                print(f"[Tick {current_tick}] Renderer.update: Error getting/drawing sprite for EID {entity_id}: {e}")
                continue

            # Log for one agent to reduce spam
            if entity_id == 2 and tm and tm.tick_counter % 20 == 0 :
                 pass # print(f"[Tick {current_tick}] Render EID {entity_id}: WorldPos({pos.x},{pos.y}) | Cam({self.camera_world_x:.1f},{self.camera_world_y:.1f}) | Zoom {self.zoom:.2f} -> ScreenBlit({screen_x_blit},{screen_y_blit})")


        # 3. Render UI Overlays (FPS, Debug Text)
        fps_text = "FPS: --"
        if observer._tick_durations:
            avg_duration = sum(observer._tick_durations) / len(observer._tick_durations)
            current_fps = 1.0 / avg_duration if avg_duration > 0 else float("inf")
            fps_text = f"{current_fps:.1f} FPS"

        if getattr(world, "fps_enabled", False) or getattr(observer, "_live_fps", False) :
            self.window.draw_text(fps_text, 5, 5, (255,255,255))

        num_entities = len(em.all_entities) if em else 'N/A'
        cam_text = f"Cam({self.camera_world_x:.1f},{self.camera_world_y:.1f}) Zoom:{self.zoom:.2f} Ents:{num_entities} Tick:{current_tick}"
        self.window.draw_text(cam_text, 5, 25, (200,200,200))

__all__ = ["Renderer"]