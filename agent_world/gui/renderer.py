"""Renderer for drawing entities to a :class:`Window`."""

from __future__ import annotations

from typing import Any

import pygame

from ..core.components.position import Position
from ..utils.asset_generation import sprite_gen
from ..utils import observer

from .window import Window


class Renderer:
    """Minimal renderer dispatching drawing to a :class:`Window`."""

    def __init__(self, window: Window | None = None) -> None:
        self.window = window if window is not None else Window()
        self.center = [0.0, 0.0]
        self.zoom = 1.0

    def update(self, world: Any) -> None:
        """Render the current state of ``world``."""

        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None:
            return

        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_LEFT:
                    self.center[0] -= 1
                elif ev.key == pygame.K_RIGHT:
                    self.center[0] += 1
                elif ev.key == pygame.K_UP:
                    self.center[1] -= 1
                elif ev.key == pygame.K_DOWN:
                    self.center[1] += 1
            elif ev.type == pygame.MOUSEWHEEL:
                self.zoom *= 1.0 + ev.y * 0.1
                self.zoom = max(self.zoom, 0.1)

        tile_w, tile_h = sprite_gen.SPRITE_SIZE

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue
            sprite = sprite_gen.get_sprite(entity_id)
            x = int((pos.x - self.center[0]) * tile_w * self.zoom)
            y = int((pos.y - self.center[1]) * tile_h * self.zoom)
            self.window.draw_sprite(entity_id, x, y, sprite)

        if observer._tick_durations:
            avg = sum(observer._tick_durations) / len(observer._tick_durations)
            fps = 1.0 / avg if avg > 0 else float("inf")
            text = f"{fps:.1f} FPS"
        else:
            text = "FPS: --"
        self.window.draw_text(text, 5, 5)



__all__ = ["Renderer"]
