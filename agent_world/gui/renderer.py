
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
ENTITY_OUTLINE_COLOR = (255, 100, 100) # A distinct color for entity outlines

class Renderer:
    """Minimal renderer dispatching drawing to a :class:`Window`."""

    def __init__(self, window: Window | None = None) -> None:
        self.window = window if window is not None else Window()
        self.camera_world_x: float = 0.0
        self.camera_world_y: float = 0.0
        self.zoom: float = 16.0
        self.min_zoom = 4.0
        self.max_zoom = 64.0
        self.debug_font = pygame.font.SysFont(None, 18)
        if self.window and not pygame.font.get_init():
            pygame.font.init()
        try:
            self.tile_font = pygame.font.SysFont(None, int(self.zoom * 0.6))
        except Exception:
             self.tile_font = pygame.font.Font(None, 12)
        self._update_tile_font_size() # Call it once on init
        self._last_world: Any | None = None

    def _update_tile_font_size(self):
        try:
            font_size = max(4, int(self.zoom * 0.5)) # Ensure minimum font size for readability
            self.tile_font = pygame.font.SysFont(None, font_size)
        except Exception:
            self.tile_font = pygame.font.Font(None, max(4, int(self.zoom * 0.5)))


    def set_camera_center(self, world_x: float, world_y: float):
        self.camera_world_x = world_x
        self.camera_world_y = world_y

    def adjust_zoom(self, factor: float):
        old_zoom = self.zoom
        mouse_screen_pos = pygame.mouse.get_pos()
        mouse_world_x_before, mouse_world_y_before = self.screen_to_world_coords(mouse_screen_pos)

        self.zoom *= factor
        self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom))
        self._update_tile_font_size()

        if abs(old_zoom - self.zoom) > 0.001:
            mouse_world_x_after, mouse_world_y_after = self.screen_to_world_coords(mouse_screen_pos)
            self.camera_world_x += (mouse_world_x_before - mouse_world_x_after)
            self.camera_world_y += (mouse_world_y_before - mouse_world_y_after)


    def pan_camera(self, dx_screen: float, dy_screen: float):
        self.camera_world_x -= dx_screen / self.zoom
        self.camera_world_y -= dy_screen / self.zoom


    def center_on_entity(self, entity_id: int) -> None:
        """Center the camera on the given entity using the last known world."""
        world = getattr(self, "_last_world", None)
        if world is None:
            return
        cm = getattr(world, "component_manager", None)
        if cm is None:
            return
        pos = cm.get_component(entity_id, Position)
        if pos is None:
            return
        self.set_camera_center(float(pos.x), float(pos.y))


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
        dx_pixels = screen_x - screen_center_px_x
        dy_pixels = screen_y - screen_center_px_y
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
        
        screen_w_world = self.window.size[0] / self.zoom
        screen_h_world = self.window.size[1] / self.zoom

        min_vis_wx = math.floor(self.camera_world_x - screen_w_world / 2) -1 
        max_vis_wx = math.ceil(self.camera_world_x + screen_w_world / 2) +1
        min_vis_wy = math.floor(self.camera_world_y - screen_h_world / 2) -1
        max_vis_wy = math.ceil(self.camera_world_y + screen_h_world / 2) +1

        tile_screen_size = int(max(1, self.zoom)) # Ensure tile screen size is at least 1

        from ..systems.movement.pathfinding import OBSTACLES as pathfinding_obstacles

        for wy in range(min_vis_wy, max_vis_wy + 1): # Inclusive max for ceil
            if not (0 <= wy < world_height): continue
            for wx in range(min_vis_wx, max_vis_wx + 1): # Inclusive max for ceil
                if not (0 <= wx < world_width): continue

                tile_data = tile_map[wy][wx] 
                screen_x, screen_y = self.world_to_screen(float(wx), float(wy))

                color = TILE_COLOR_MAP["default"]
                glyph = None 

                if (wx, wy) in pathfinding_obstacles: 
                    color = TILE_COLOR_MAP["obstacle"]
                    glyph = "#" 
                elif tile_data and isinstance(tile_data, dict):
                    kind = tile_data.get("kind")
                    color = TILE_COLOR_MAP.get(kind, color)
                    glyph = tile_data.get("glyph")
                
                pygame.draw.rect(self.window._surface, color, (screen_x, screen_y, tile_screen_size, tile_screen_size))
                
                if glyph and self.tile_font and self.zoom > 6: # Only draw glyphs if font exists & reasonably zoomed
                    text_surf = self.tile_font.render(str(glyph), True, DEFAULT_TILE_GLYPH_COLOR)
                    text_rect = text_surf.get_rect(center=(screen_x + tile_screen_size // 2, screen_y + tile_screen_size // 2))
                    self.window._surface.blit(text_surf, text_rect)

    def update(self, world: Any) -> None:
        tm = getattr(world, "time_manager", None)
        current_tick = tm.tick_counter if tm else "N/A"
        self._last_world = world

        if self.window is None or not hasattr(self.window, '_surface'):
            return

        self._render_tiles(world) # Render background tiles first

        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None:
            return

        entity_render_details = [] # For debug

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue

            try:
                # Get the base PIL image for the sprite, with an outline
                base_sprite_pil = sprite_gen.get_sprite(entity_id, outline_colour=ENTITY_OUTLINE_COLOR)
                
                # Entities are 1x1 world units. Their screen size is determined by zoom.
                sprite_screen_width = int(max(1, self.zoom)) # Ensure at least 1 pixel
                sprite_screen_height = int(max(1, self.zoom))

                screen_x_blit, screen_y_blit = self.world_to_screen(float(pos.x), float(pos.y))
                
                self.window.draw_sprite_scaled(entity_id, screen_x_blit, screen_y_blit, base_sprite_pil, 
                                               (sprite_screen_width, sprite_screen_height))
                
                if entity_id in [2,3,4] and tm and tm.tick_counter % 60 == 0 : # Log for specific entities periodically
                     detail = (f"EID {entity_id}: World({pos.x},{pos.y}) "
                               f"-> Screen({screen_x_blit},{screen_y_blit}) "
                               f"Size({sprite_screen_width}x{sprite_screen_height})")
                     entity_render_details.append(detail)

            except Exception as e:
                print(f"[Tick {current_tick}] Renderer.update: Error getting/drawing sprite for EID {entity_id}: {e}")
                continue
        
        if entity_render_details:
            print(f"[Tick {current_tick}] Entity Render Details (Zoom: {self.zoom:.2f}):")
            for detail in entity_render_details:
                print(f"  {detail}")


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