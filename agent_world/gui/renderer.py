"""Stub renderer for GUI integration."""

from __future__ import annotations

from typing import Any

from .window import Window


class Renderer:
    """Minimal renderer dispatching drawing to a :class:`Window`."""

    def __init__(self, window: Window | None = None) -> None:
        self.window = window if window is not None else Window()

    def update(self, world: Any) -> None:
        """Render the current state of ``world`` (no-op)."""

        # No-op stub implementation
        return None


__all__ = ["Renderer"]
