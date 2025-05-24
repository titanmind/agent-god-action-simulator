
"""Simple ``pygame`` window for rendering sprites and text."""

from __future__ import annotations

from typing import Any
from pathlib import Path
import os

import yaml
import pygame
from PIL import Image


def _load_window_size(config_path: Path) -> tuple[int, int]:
    """Return window size from ``config.yaml`` if present."""

    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            cfg: dict[str, Any] = yaml.safe_load(fh) or {}
    except Exception:  # pragma: no cover - config missing/malformed
        return 800, 600

    gui_cfg = cfg.get("gui", {}) if isinstance(cfg, dict) else {}
    size_from_cfg = gui_cfg.get("window_size") or gui_cfg.get("size") # Check "gui" section first
    if not size_from_cfg and isinstance(cfg, dict) : # Fallback to root level
        size_from_cfg = cfg.get("window_size")


    if isinstance(size_from_cfg, (list, tuple)) and len(size_from_cfg) >= 2:
        try:
            return int(size_from_cfg[0]), int(size_from_cfg[1])
        except Exception:  # pragma: no cover - invalid values
            return 800, 600

    return 800, 600


class Window:
    """``pygame`` backed drawing surface."""

    def __init__(self, size: tuple[int, int] | None = None, *, resizable: bool = True) -> None:
        # Consider removing or commenting out this line if GUI doesn't appear:
        # os.environ.setdefault("SDL_VIDEODRIVER", os.environ.get("SDL_VIDEODRIVER", "dummy"))

        if size is None:
            project_root_config = Path("config.yaml")
            size = _load_window_size(project_root_config)


        self.size = size
        flags = pygame.RESIZABLE if resizable else 0
        
        if not pygame.get_init():
             pygame.init() 
        if not pygame.font.get_init():
            pygame.font.init() 
        if not pygame.display.get_init():
            pygame.display.init() 

        self._surface = pygame.display.set_mode(self.size, flags)
        pygame.display.set_caption("Agent World")
        
        try:
            self._font = pygame.font.SysFont(None, 24) 
        except pygame.error: 
             self._font = pygame.font.Font(None, 24) 


        self._sprite_cache: dict[int, pygame.Surface] = {}

    def _image_to_surface(self, pil_image: Image.Image) -> pygame.Surface:
        mode = pil_image.mode
        data = pil_image.tobytes()
        size = pil_image.size 
        surf = pygame.image.frombuffer(data, size, mode)
        if "A" in mode: 
            return surf.convert_alpha()
        return surf.convert()

    def draw_sprite(self, entity_id: int, x: int, y: int, pil_image: Image.Image) -> None:
        surf = self._sprite_cache.get(entity_id)
        if surf is None:
            surf = self._image_to_surface(pil_image)
            self._sprite_cache[entity_id] = surf
        self._surface.blit(surf, (x, y))

    def draw_text(
        self, text: str, x: int, y: int, colour: tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        text_surf = self._font.render(text, True, colour)
        self._surface.blit(text_surf, (x, y))

    def refresh(self) -> None:
        pygame.display.flip()
        # pygame.event.pump() # Event pumping should be handled by the main loop or input handler.
                              # Avoid pumping here to prevent conflicts.

    def clear(self, color: tuple[int,int,int] = (0,0,0)) -> None:
        """Clears the window with a given color."""
        self._surface.fill(color)

__all__ = ["Window"]