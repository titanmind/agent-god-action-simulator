"""Lightweight file-watcher for generated abilities."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable, Dict


def watch_generated(
    on_change: Callable[[Path], None], interval: float = 1.0
) -> threading.Thread:
    """Start a daemon thread watching ``abilities/generated`` for changes.

    Parameters
    ----------
    on_change:
        Callback invoked with the path of each changed ``.py`` file.
    interval:
        Polling interval in seconds. Defaults to ``1.0``.

    Returns
    -------
    threading.Thread
        The watcher thread which has already been started.
    """

    base_dir = Path(__file__).resolve().parents[2] / "abilities" / "generated"
    mtimes: Dict[Path, float] = {
        p: p.stat().st_mtime for p in base_dir.glob("*.py") if p.is_file()
    }

    def _loop() -> None:
        while True:
            for path in base_dir.glob("*.py"):
                try:
                    mtime = path.stat().st_mtime
                except FileNotFoundError:  # pragma: no cover - race condition
                    continue
                last = mtimes.get(path)
                if last is None or mtime != last:
                    mtimes[path] = mtime
                    try:
                        on_change(path)
                    except Exception as exc:  # pragma: no cover - background err
                        print(f"Hot-reload callback failed: {exc}")

            for tracked in list(mtimes.keys()):
                if not tracked.exists():
                    mtimes.pop(tracked, None)

            time.sleep(interval)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


__all__ = ["watch_generated"]
