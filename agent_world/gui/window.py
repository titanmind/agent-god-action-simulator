
# agent_world/gui/window.py
"""Simple ``pygame`` window for rendering sprites and text."""

from __future__ import annotations

from typing import Any, Optional
from pathlib import Path
import os
from collections import OrderedDict # For LRU cache

import yaml
import pygame
from PIL import Image


def _load_window_size(config_path: Path) -> tuple[int, int]:
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            cfg: dict[str, Any] = yaml.safe_load(fh) or {}
    except Exception:
        return 800, 600
    gui_cfg = cfg.get("gui", {}) if isinstance(cfg, dict) else {}
    size_from_cfg = gui_cfg.get("window_size") or gui_cfg.get("size")
    if not size_from_cfg and isinstance(cfg, dict) :
        size_from_cfg = cfg.get("window_size")
    if isinstance(size_from_cfg, (list, tuple)) and len(size_from_cfg) >= 2:
        try:
            return int(size_from_cfg[0]), int(size_from_cfg[1])
        except Exception:
            return 800, 600
    return 800, 600


class Window:
    """``pygame`` backed drawing surface."""
    # Max number of distinct scaled surfaces to cache.
    # Each entity at each distinct scaled size counts as one entry.
    MAX_SCALED_SURFACES_CACHE_SIZE = 500 

    def __init__(self, size: tuple[int, int] | None = None, *, resizable: bool = True) -> None:
        if size is None:
            project_root_config = Path("config.yaml")
            if not project_root_config.exists():
                project_root_config = Path(__file__).resolve().parents[2] / "config.yaml"
            size = _load_window_size(project_root_config)

        self.size = size
        flags = pygame.RESIZABLE if resizable else 0
        
        if not pygame.get_init(): pygame.init()
        if not pygame.font.get_init(): pygame.font.init()
        if not pygame.display.get_init(): pygame.display.init()

        self._surface = pygame.display.set_mode(self.size, flags)
        pygame.display.set_caption("Agent World")
        
        try:
            self._font = pygame.font.SysFont(None, 24)
        except pygame.error:
             self._font = pygame.font.Font(None, 24)

        self._pil_to_surface_cache: dict[int, pygame.Surface] = {}
        self._scaled_surface_cache: OrderedDict[tuple[int, int, int], pygame.Surface] = OrderedDict()


    def _get_base_surface(self, entity_id: int, pil_image: Image.Image) -> pygame.Surface:
        if entity_id in self._pil_to_surface_cache:
            return self._pil_to_surface_cache[entity_id]

        mode = pil_image.mode
        data = pil_image.tobytes()
        img_size = pil_image.size
        surf = pygame.image.frombuffer(data, img_size, mode)
        
        converted_surf = surf.convert_alpha() if "A" in mode else surf.convert()
        self._pil_to_surface_cache[entity_id] = converted_surf
        # Simple cache eviction for base surfaces if needed, though less critical than scaled
        if len(self._pil_to_surface_cache) > 200: # Example limit
             self._pil_to_surface_cache.pop(next(iter(self._pil_to_surface_cache)))
        return converted_surf

    def draw_sprite(self, entity_id: int, x: int, y: int, pil_image: Image.Image) -> None:
        surf = self._get_base_surface(entity_id, pil_image)
        self._surface.blit(surf, (x, y))

    def draw_sprite_scaled(self, entity_id: int, x: int, y: int, pil_image: Image.Image, target_size: tuple[int,int]) -> None:
        scaled_width, scaled_height = target_size
        if scaled_width <= 0 or scaled_height <= 0: return

        cache_key = (entity_id, scaled_width, scaled_height)
        
        scaled_surf = self._scaled_surface_cache.get(cache_key)

        if scaled_surf is None:
            base_surf = self._get_base_surface(entity_id, pil_image)
            try:
                # Using smoothscale can be slow. For pixel art, 'scale' might be better if aliasing is ok.
                scaled_surf = pygame.transform.smoothscale(base_surf, (scaled_width, scaled_height))
            except pygame.error as e: # Handle cases where scaling might fail (e.g. to 0x0)
                print(f"Error scaling surface for EID {entity_id} to {target_size}: {e}")
                # Draw base_surf unscaled as a fallback or a placeholder
                self._surface.blit(base_surf, (x,y)) 
                return

            self._scaled_surface_cache[cache_key] = scaled_surf
            if len(self._scaled_surface_cache) > self.MAX_SCALED_SURFACES_CACHE_SIZE:
                self._scaled_surface_cache.popitem(last=False) # Pop oldest
        else:
            # Move to end to signify recent use for LRU
            self._scaled_surface_cache.move_to_end(cache_key)


        self._surface.blit(scaled_surf, (x, y))


    def draw_text(
        self, text: str, x: int, y: int, colour: tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        if not self._font: return
        text_surf = self._font.render(text, True, colour)
        self._surface.blit(text_surf, (x, y))

    def refresh(self) -> None:
        pygame.display.flip()

    def clear(self, color: tuple[int,int,int] = (0,0,0)) -> None:
        self._surface.fill(color)

__all__ = ["Window"]