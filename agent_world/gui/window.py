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
    size = gui_cfg.get("window_size") or gui_cfg.get("size") or cfg.get("window_size")

    if isinstance(size, (list, tuple)) and len(size) >= 2:
        try:
            return int(size[0]), int(size[1])
        except Exception:  # pragma: no cover - invalid values
            return 800, 600

    return 800, 600


class Window:
    """``pygame`` backed drawing surface."""

    def __init__(self, size: tuple[int, int] | None = None, *, resizable: bool = True) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", os.environ.get("SDL_VIDEODRIVER", "dummy"))

        if size is None:
            size = _load_window_size(Path("config.yaml"))

        self.size = size
        flags = pygame.RESIZABLE if resizable else 0
        pygame.display.init()
        pygame.font.init()
        self._surface = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("Agent World")
        self._font = pygame.font.SysFont(None, 16)
        self._sprite_cache: dict[int, pygame.Surface] = {}

    def _image_to_surface(self, pil_image: Image.Image) -> pygame.Surface:
        mode = pil_image.mode
        data = pil_image.tobytes()
        surf = pygame.image.frombuffer(data, pil_image.size, mode)
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
        pygame.event.pump()


__all__ = ["Window"]
