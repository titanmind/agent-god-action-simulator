import types

from agent_world.utils.cli import commands, terminal_view
from agent_world.core.time_manager import TimeManager


def _make_world():
    size = (10, 10)
    tile_map = [[None for _ in range(size[0])] for _ in range(size[1])]
    tm = TimeManager(tick_rate=1000.0)
    tm.sleep_until_next_tick = lambda: None  # type: ignore[assignment]
    return types.SimpleNamespace(size=size, tile_map=tile_map, time_manager=tm)


def test_view_command_toggles_and_renders(monkeypatch):
    world = _make_world()
    view = terminal_view.get_view()
    view.enabled = False
    view.radius = 0
    calls: list[int] = []
    monkeypatch.setattr(view, "render", lambda w: calls.append(1))

    state: dict[str, bool] = {}
    commands.execute("view", ["3"], world, state)
    assert state["view"] is True
    assert view.enabled
    assert view.radius == 3

    world.time_manager.sleep_until_next_tick()
    # First render happens on toggle, second via the tick hook
    assert calls == [1, 1]

    commands.execute("view", [], world, state)
    assert state["view"] is False
    assert not view.enabled
