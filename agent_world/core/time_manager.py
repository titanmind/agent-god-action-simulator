"""Tick timing helpers."""

from __future__ import annotations

import time


class TimeManager:
    """Manage the game tick cadence."""

    def __init__(self, tick_rate: float = 10.0) -> None:
        self.tick_rate: float = tick_rate
        self.tick_counter: int = 0
        self._last_tick: float = time.perf_counter()

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------
    def sleep_until_next_tick(self) -> None:
        """Block until the next tick should occur."""

        interval = 1.0 / self.tick_rate
        target = self._last_tick + interval
        now = time.perf_counter()
        remaining = target - now
        if remaining > 0:
            time.sleep(remaining)
            self._last_tick = target
        else:
            # We're behind schedule; start from current time
            self._last_tick = now
        self.tick_counter += 1


__all__ = ["TimeManager"]
