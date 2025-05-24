"""Implementations of development CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from ...persistence.save_load import save_world
from ..observer import install_tick_observer, toggle_live_fps

try:  # utils.profiling may not implement profile_ticks yet
    from ..profiling import profile_ticks
except Exception:  # pragma: no cover - fallback for placeholder module

    def profile_ticks(world: Any, ticks: int) -> None:
        pass


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")


def pause(state: Dict[str, Any]) -> None:
    """Set ``state['paused']`` to ``True``."""

    state["paused"] = True


def step(state: Dict[str, Any]) -> None:
    """Request a single tick while paused."""

    state["step"] = True


def save(world: Any, path: str | Path | None = None) -> None:
    """Serialize ``world`` to ``path`` or ``DEFAULT_SAVE_PATH``."""

    save_world(world, Path(path) if path is not None else DEFAULT_SAVE_PATH)


def reload_abilities(world: Any) -> None:
    """Force ability hot-reload by calling ``update`` on the ability system."""

    sm: Iterable[Any] | None = getattr(world, "systems_manager", None)
    if sm is None:
        return
    for system in sm:
        if hasattr(system, "abilities"):
            update = getattr(system, "update", None)
            if callable(update):
                update()


def profile(world: Any, ticks: int) -> None:
    """Run :func:`profile_ticks` for ``ticks``."""

    profile_ticks(world, ticks)


def fps(world: Any, state: Dict[str, Any]) -> None:
    """Toggle live FPS printing for the tick loop."""

    tm = getattr(world, "time_manager", None)
    if tm is not None:
        install_tick_observer(tm)
    state["fps"] = toggle_live_fps()


def execute(command: str, args: list[str], world: Any, state: Dict[str, Any]) -> None:
    """Dispatch ``command`` with ``args``."""

    if command == "pause":
        pause(state)
    elif command == "step":
        step(state)
    elif command == "save":
        save(world, args[0] if args else None)
    elif command == "reload" and args and args[0] == "abilities":
        reload_abilities(world)
    elif command == "profile":
        profile(world, int(args[0]) if args else 1)
    elif command == "fps":
        fps(world, state)


__all__ = [
    "pause",
    "step",
    "save",
    "reload_abilities",
    "profile",
    "fps",
    "execute",
]
