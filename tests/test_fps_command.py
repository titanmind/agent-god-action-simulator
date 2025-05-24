import types

from agent_world.utils.cli import commands
from agent_world.utils import observer
from agent_world.core.time_manager import TimeManager


def _make_world():
    tm = TimeManager(tick_rate=1000.0)
    tm.sleep_until_next_tick = lambda: None  # type: ignore[assignment]
    return types.SimpleNamespace(time_manager=tm)


def test_fps_command_toggles_and_prints(monkeypatch):
    world = _make_world()
    calls: list[int] = []
    monkeypatch.setattr(observer, "print_fps", lambda: calls.append(1))

    state: dict[str, bool] = {}
    commands.execute("fps", [], world, state)
    assert state["fps"] is True

    world.time_manager.sleep_until_next_tick()
    assert calls == [1]

    commands.execute("fps", [], world, state)
    assert state["fps"] is False

    calls.clear()
    world.time_manager.sleep_until_next_tick()
    assert calls == []
