"""Incremental snapshot utilities."""

from __future__ import annotations

import gzip
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from .serializer import world_from_dict, world_to_dict
from .save_load import load_world


# Cache of last saved state per increments directory
# {dir_path: (state_dict, last_tick)}
_CACHE: Dict[Path, Tuple[Dict[str, Any], int]] = {}


def _diff(old: Any, new: Any) -> Any:
    """Return a nested diff between ``old`` and ``new``."""

    if old == new:
        return None
    if isinstance(old, dict) and isinstance(new, dict):
        out = {}
        keys = set(old.keys()) | set(new.keys())
        for k in keys:
            if k in new and k in old:
                d = _diff(old[k], new[k])
                if d is not None:
                    out[k] = d
            elif k in new:
                out[k] = new[k]
            else:
                # Key removed; store sentinel by omitting from diff
                out[k] = None
        return out
    return new


def _apply(data: Dict[str, Any], delta: Dict[str, Any]) -> None:
    """Apply ``delta`` onto ``data`` in-place."""

    for k, v in delta.items():
        if isinstance(v, dict) and isinstance(data.get(k), dict):
            _apply(data[k], v)  # type: ignore[arg-type]
        elif v is None:
            data.pop(k, None)
        else:
            data[k] = v


def _write_json_gz(path: Path, obj: Any) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh)


def _read_json_gz(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def save_incremental(
    world: "World", increments_dir: str | Path, *, tick_interval: int = 5
) -> None:
    """Persist a delta snapshot if ``tick_interval`` has passed."""

    tm = getattr(world, "time_manager", None)
    if tm is None:
        return
    tick = tm.tick_counter
    dir_path = Path(increments_dir)
    if dir_path not in _CACHE:
        current = world_to_dict(world)
        file_path = dir_path / f"{tick:07d}.json.gz"
        _write_json_gz(file_path, current)
        _CACHE[dir_path] = (current, tick)
        return

    state, last = _CACHE[dir_path]
    if tick - last < tick_interval:
        return

    current = world_to_dict(world)
    delta = _diff(state, current) or {}
    file_path = dir_path / f"{tick:07d}.json.gz"
    _write_json_gz(file_path, delta)
    _CACHE[dir_path] = (current, tick)


def start_incremental_save(
    world: "World",
    increments_dir: str | Path,
    *,
    tick_interval: int = 5,
    poll_interval: float = 0.1,
) -> None:
    """Start a daemon thread that writes incremental snapshots."""

    dir_path = Path(increments_dir)

    def _loop() -> None:
        while True:
            save_incremental(world, dir_path, tick_interval=tick_interval)
            time.sleep(poll_interval)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def load_incremental(path: str | Path) -> "World":
    """Load world state reconstructed up to the incremental snapshot at ``path``."""

    inc_path = Path(path)
    base_path = inc_path.parent.parent / "world_state.json.gz"
    world = load_world(base_path)
    state = world_to_dict(world)
    for p in sorted(inc_path.parent.glob("*.json.gz")):
        delta = _read_json_gz(p)
        _apply(state, delta)
        if p == inc_path:
            break
    return world_from_dict(state)


__all__ = [
    "save_incremental",
    "start_incremental_save",
    "load_incremental",
]
