"""Runtime observability helpers."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Deque

from ..persistence.serializer import world_to_dict

# Rolling history of the last 1000 tick durations in seconds
_TICK_HISTORY_LEN = 1000
_tick_durations: Deque[float] = deque(maxlen=_TICK_HISTORY_LEN)


def record_tick(duration: float) -> None:
    """Append a tick ``duration`` in seconds to the rolling history."""

    _tick_durations.append(duration)


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


def dump_state(world: "World", path: str | Path) -> None:
    """Write ``world`` state to ``path`` as JSON for offline inspection."""

    data = world_to_dict(world)
    p = Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


__all__ = [
    "record_tick",
    "print_fps",
    "dump_state",
    "_tick_durations",
]
