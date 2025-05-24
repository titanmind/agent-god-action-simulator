"""ASCII terminal renderer for world tile maps."""

from __future__ import annotations

import sys
from typing import Any, Sequence


# Basic ANSI colour codes used by :class:`TerminalView`
_COLOURS = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    "reset": "\x1b[0m",
}


class TerminalView:
    """Minimal tile map viewer using ANSI colours."""

    def __init__(self, width: int = 40, height: int = 20) -> None:
        self.width = width
        self.height = height
        self.enabled: bool = False
        self.radius: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def toggle(self, radius: int | None = None) -> bool:
        """Toggle rendering and optionally set ``radius``."""

        self.enabled = not self.enabled
        if radius is not None:
            self.radius = int(radius)
        return self.enabled

    def render(self, world: Any, center: tuple[int, int] | None = None) -> None:
        """Draw a 40×20 chunk of ``world.tile_map`` to ``stdout``."""

        if not self.enabled:
            return

        if center is None:
            cx, cy = world.size[0] // 2, world.size[1] // 2
        else:
            cx, cy = center

        half_w = self.width // 2
        half_h = self.height // 2
        start_x = max(0, cx - half_w)
        start_y = max(0, cy - half_h)
        end_x = min(world.size[0], start_x + self.width)
        end_y = min(world.size[1], start_y + self.height)

        lines: list[str] = []
        for y in range(start_y, end_y):
            row: list[str] = []
            for x in range(start_x, end_x):
                tile = world.tile_map[y][x]
                glyph, colour = _tile_to_glyph_colour(tile)
                row.append(f"{_COLOURS.get(colour, '')}{glyph}")
            row.append(_COLOURS["reset"])
            lines.append("".join(row))

        sys.stdout.write("\x1b[H\x1b[2J")  # clear screen
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _tile_to_glyph_colour(tile: Any) -> tuple[str, str]:
    glyph = "."
    colour = "reset"
    if tile is None:
        return glyph, colour
    if isinstance(tile, dict):
        glyph = str(tile.get("glyph", glyph))
        colour = tile.get("colour", tile.get("color", colour))
    else:
        glyph = str(getattr(tile, "glyph", glyph))
        colour = getattr(tile, "colour", getattr(tile, "color", colour))
    glyph = glyph[:1] if glyph else "."
    return glyph, str(colour)


_view = TerminalView()


def get_view() -> TerminalView:
    """Return the singleton :class:`TerminalView` instance."""

    return _view


# ----------------------------------------------------------------------
# CLI integration
# ----------------------------------------------------------------------


def _install_tick_hook(world: Any) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None or hasattr(tm, "_terminal_view_wrapped"):
        return

    original = tm.sleep_until_next_tick

    def wrapper() -> None:
        original()
        _view.render(world)

    tm.sleep_until_next_tick = wrapper  # type: ignore[assignment]
    setattr(tm, "_terminal_view_wrapped", True)


def _view_command(args: Sequence[str], world: Any, state: dict[str, Any]) -> None:
    radius = int(args[0]) if args else None
    state["view"] = _view.toggle(radius)
    _install_tick_hook(world)
    if _view.enabled:
        _view.render(world)


def _patch_commands() -> None:
    from . import commands

    if getattr(commands, "_terminal_view_patched", False):
        return

    original = commands.execute

    def execute(
        command: str, args: list[str], world: Any, state: dict[str, Any]
    ) -> None:
        if command == "view":
            _view_command(args, world, state)
        else:
            original(command, args, world, state)

    commands.execute = execute  # type: ignore[assignment]
    setattr(commands, "_terminal_view_patched", True)


_patch_commands()


__all__ = ["TerminalView", "get_view"]
