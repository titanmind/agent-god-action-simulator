import builtins
from agent_world.utils import observer
from agent_world.core.world import World


def test_warn_missing_managers_once(capsys):
    world = World((3, 3))
    observer._missing_manager_warned = False
    observer.warn_missing_managers(world)
    out1 = capsys.readouterr().out
    assert "manager" in out1
    observer.warn_missing_managers(world)
    out2 = capsys.readouterr().out
    assert out2 == ""


def test_log_event_helpers():
    log = []
    observer.log_event("collision", {"entity": 1, "pos": (0, 0)}, log)
    assert log == [{"type": "collision", "entity": 1, "pos": (0, 0)}]
    observer._events.clear()
    observer.log_event("move_blocked", {"entity": 2, "pos": (1, 0)})
    assert observer._events[-1] == {"type": "move_blocked", "entity": 2, "pos": (1, 0)}


def test_average_fps():
    observer._tick_durations.clear()
    observer._tick_durations.extend([0.1, 0.1])
    assert observer.average_fps() == 10.0
