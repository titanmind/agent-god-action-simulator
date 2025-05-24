import types

from agent_world.utils.cli import commands
from agent_world.core.time_manager import TimeManager


def _make_world():
    tm = TimeManager(tick_rate=1000.0)
    tm.sleep_until_next_tick = lambda: None  # type: ignore[assignment]
    return types.SimpleNamespace(time_manager=tm)


def test_gui_command_toggles_and_updates(monkeypatch):
    world = _make_world()
    calls: list[str] = []
    monkeypatch.setattr(commands._renderer, "update", lambda w: calls.append("u"))
    monkeypatch.setattr(commands._renderer.window, "refresh", lambda: calls.append("r"))

    state: dict[str, bool] = {}
    commands.execute("gui", [], world, state)
    assert state["gui_enabled"] is True

    world.time_manager.sleep_until_next_tick()
    assert calls == ["u", "r", "u", "r"]

    commands.execute("gui", [], world, state)
    assert state["gui_enabled"] is False

    calls.clear()
    world.time_manager.sleep_until_next_tick()
    assert calls == []
