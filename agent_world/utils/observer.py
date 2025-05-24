"""Runtime observability helpers."""

from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List

from ..persistence.serializer import world_to_dict

# Rolling history of the last 1000 tick durations in seconds
_TICK_HISTORY_LEN = 1000
_tick_durations: Deque[float] = deque(maxlen=_TICK_HISTORY_LEN)

# Whether to print FPS every tick when recording durations
_live_fps: bool = False

# Global in-memory list for logged events when no destination is supplied
_events: List[Dict[str, Any]] = []

# Track whether we've already warned about missing managers
_missing_manager_warned: bool = False


def record_tick(duration: float) -> None:
    """Append a tick ``duration`` in seconds to the rolling history."""

    _tick_durations.append(duration)
    if _live_fps:
        print_fps()


def print_fps() -> None:
    """Print average FPS and tick time based on recorded durations."""

    if not _tick_durations:
        print("FPS: --")
        return

    avg = sum(_tick_durations) / len(_tick_durations)
    fps = 1.0 / avg if avg > 0 else float("inf")
    msg = f"{fps:.1f} FPS (avg {avg*1000:.1f} ms)"
    if _tick_durations[-1] > 0.1:
        msg += " - tick over budget"
    print(msg)


def toggle_live_fps() -> bool:
    """Toggle live FPS printing. Returns ``True`` if enabled after toggle."""

    global _live_fps
    _live_fps = not _live_fps
    return _live_fps


def install_tick_observer(tm: Any) -> None:
    """Wrap ``tm.sleep_until_next_tick`` to record tick durations."""

    if tm is None or hasattr(tm, "_observer_wrapped"):
        return

    original = tm.sleep_until_next_tick
    last = time.perf_counter()

    def wrapper() -> None:
        nonlocal last
        original()
        now = time.perf_counter()
        record_tick(now - last)
        last = now

    tm.sleep_until_next_tick = wrapper  # type: ignore[assignment]
    setattr(tm, "_observer_wrapped", True)


def warn_missing_managers(world: Any) -> None:
    """Print a warning once if any ``*_manager`` attribute is ``None``."""

    global _missing_manager_warned
    if _missing_manager_warned:
        return

    missing = [
        name
        for name in dir(world)
        if name.endswith("_manager") and getattr(world, name, None) is None
    ]
    if missing:
        joined = ", ".join(sorted(missing))
        print(f"Warning: world has uninitialized managers: {joined}")
        _missing_manager_warned = True


def dump_state(world: "World", path: str | Path) -> None:
    """Write ``world`` state to ``path`` as JSON for offline inspection."""

    data = world_to_dict(world)
    p = Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def log_event(
    event_type: str,
    data: Dict[str, Any],
    log: List[Dict[str, Any]] | None = None,
) -> None:
    """Append an event dict to ``log`` or the internal event buffer."""

    event = {"type": event_type}
    event.update(data)
    if log is None:
        _events.append(event)
    else:
        log.append(event)


__all__ = [
    "record_tick",
    "print_fps",
    "toggle_live_fps",
    "install_tick_observer",
    "warn_missing_managers",
    "log_event",
    "dump_state",
    "_tick_durations",
    "_events",
]
