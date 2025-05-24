"""cProfile helpers for measuring tick performance."""

from __future__ import annotations

import cProfile
import pstats
from pathlib import Path
from typing import Callable
import time

from .observer import record_tick


def profile_ticks(
    n: int,
    tick_callback: Callable[[], None],
    out_path: str | Path = "profile.prof",
) -> pstats.Stats:
    """Profile ``tick_callback`` for ``n`` iterations and dump stats to ``out_path``.

    Parameters
    ----------
    n:
        Number of iterations to profile.
    tick_callback:
        Function called once per tick.
    out_path:
        File to write cProfile data to.

    Returns
    -------
    pstats.Stats
        Profiling statistics for the execution.
    """

    path = Path(out_path)
    profiler = cProfile.Profile()
    profiler.enable()
    last = time.perf_counter()
    for _ in range(n):
        tick_callback()
        now = time.perf_counter()
        record_tick(now - last)
        last = now
    profiler.disable()
    profiler.dump_stats(str(path))
    return pstats.Stats(profiler)


__all__ = ["profile_ticks"]
