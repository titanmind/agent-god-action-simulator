import time
import pytest

from agent_world.core.time_manager import TimeManager


def test_sleep_increments_counter():
    tm = TimeManager(tick_rate=50.0)
    start = time.perf_counter()
    tm.sleep_until_next_tick()
    elapsed = time.perf_counter() - start

    assert tm.tick_counter == 1
    # Expect roughly 20ms sleep; allow generous tolerance
    assert elapsed == pytest.approx(0.02, abs=0.01)
