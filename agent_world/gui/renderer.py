
"""Renderer for drawing entities to a :class:`Window`."""

from __future__ import annotations
from typing import Any
from ..core.components.position import Position # Uncommented
from ..utils.asset_generation import sprite_gen # Uncommented
from ..utils import observer 
from .window import Window
import pygame 

class Renderer:
    """Minimal renderer dispatching drawing to a :class:`Window`."""

    def __init__(self, window: Window | None = None) -> None:
        self.window = window if window is not None else Window()
        self.center = [0.0, 0.0] 
        self.zoom = 1.0 

    def update(self, world: Any) -> None:
        """Render the current state of ``world``."""
        if self.window is None or not hasattr(self.window, '_surface'):
            return

        # --- DEBUG DRAWING (KEEP FOR NOW) ---
        pygame.draw.rect(self.window._surface, (255, 255, 0), (50, 50, 100, 100)) # Yellow square
        self.window.draw_text("Renderer Update Test", 50, 160, (255,255,255))
        # --- END DEBUG DRAWING ---

        # --- RESTORED ENTITY DRAWING ---
        em = getattr(world, "entity_manager", None) 
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None:
            # print("Renderer.update: Entity or Component Manager not found in world.") # DEBUG
            return

        # print(f"Renderer.update: Found {len(em.all_entities)} entities. Camera: {self.center}, Zoom: {self.zoom}") # DEBUG

        tile_w, tile_h = sprite_gen.SPRITE_SIZE # Should be (32, 32)
        
        entities_drawn = 0
        for entity_id in list(em.all_entities.keys()): # Iterate over a copy of keys
            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue
            
            # Get sprite (this could be a bottleneck if many new sprites are generated)
            try:
                sprite_pil_image = sprite_gen.get_sprite(entity_id) 
            except Exception as e:
                print(f"Error getting sprite for entity {entity_id}: {e}")
                continue # Skip drawing this entity if sprite fails

            # Camera Transform: World to Screen
            # Screen X = (World X - CameraWorldXAtScreenOrigin) * Zoom
            # CameraWorldXAtScreenOrigin = CameraCenterInWorldX - (ScreenWidth / 2 / Zoom)
            # For simplicity, we are doing:
            # Offset from camera center in world units = (pos.x - self.center[0])
            # Offset in screen units = Offset from camera center in world units * (tile_w * self.zoom)
            # Final screen pos = ScreenCenter + Offset in screen units
            
            # World coordinates relative to camera's center point
            world_dx_from_cam_center = pos.x - self.center[0]
            world_dy_from_cam_center = pos.y - self.center[1]

            # Convert this delta to screen pixels, scaled by zoom and base tile size
            # Note: sprite_gen.SPRITE_SIZE is (width, height), so tile_w is correct.
            # We are assuming 1 world unit = 1 tile for this transform.
            screen_dx_from_screen_center = world_dx_from_cam_center * (tile_w * self.zoom)
            screen_dy_from_screen_center = world_dy_from_cam_center * (tile_h * self.zoom)
            
            # Position on screen, relative to screen center, then add screen center
            screen_x = (self.window.size[0] / 2) + screen_dx_from_screen_center
            screen_y = (self.window.size[1] / 2) + screen_dy_from_screen_center
            
            # Blit the sprite. The x,y for blit is top-left of the surface.
            # If our sprite is 32x32, and screen_x, screen_y is its center, adjust:
            # screen_x_topleft = screen_x - (sprite_pil_image.width / 2)
            # screen_y_topleft = screen_y - (sprite_pil_image.height / 2)
            # For now, let's assume screen_x, screen_y is the top-left for simplicity.
            # This might mean entities are drawn slightly off if tile_w/h isn't the sprite size.
            # Since sprite_gen.SPRITE_SIZE is used for tile_w/h, it should be consistent.

            # print(f"Drawing entity {entity_id} at world({pos.x},{pos.y}) -> screen({int(screen_x)},{int(screen_y)})") # DEBUG
            self.window.draw_sprite(entity_id, int(screen_x), int(screen_y), sprite_pil_image)
            entities_drawn +=1
        
        # if entities_drawn > 0: print(f"Renderer.update: Drew {entities_drawn} entities.") # DEBUG
        # elif len(em.all_entities) > 0 : print("Renderer.update: Entities exist but none drawn (check positions/camera).") # DEBUG
        # --- END RESTORED ENTITY DRAWING ---

        fps_text = "FPS: --"
        if observer._tick_durations: 
            avg_duration = sum(observer._tick_durations) / len(observer._tick_durations)
            current_fps = 1.0 / avg_duration if avg_duration > 0 else float("inf")
            fps_text = f"{current_fps:.1f} FPS"
        
        if getattr(world, "fps_enabled", False) or getattr(observer, "_live_fps", False) :
            self.window.draw_text(fps_text, 5, 5)
        
        # Debug camera info on screen
        cam_text = f"Cam:({self.center[0]:.1f},{self.center[1]:.1f}) Zoom:{self.zoom:.2f} Entities: {len(em.all_entities) if em else 'N/A'}"
        self.window.draw_text(cam_text, 5, 25, (200,200,200))


__all__ = ["Renderer"]