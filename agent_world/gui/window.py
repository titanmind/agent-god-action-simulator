"""GUI window interface."""

from __future__ import annotations

from typing import Any
from PIL import Image


class Window:
    """Abstract drawing surface for sprites and text."""

    def draw_sprite(
        self, entity_id: int, x: int, y: int, pil_image: Image.Image
    ) -> None:
        """Draw ``pil_image`` for ``entity_id`` at ``(x, y)``."""

        # No-op stub implementation
        return None

    def draw_text(
        self, text: str, x: int, y: int, colour: tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        """Draw ``text`` at ``(x, y)`` in ``colour``."""

        # No-op stub implementation
        return None

    def refresh(self) -> None:
        """Refresh the display."""

        # No-op stub implementation
        return None


__all__ = ["Window"]
