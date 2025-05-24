from agent_world.core.systems_manager import SystemsManager


class DummySystem:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def update(self, tick: int) -> None:
        self.calls.append(tick)


def test_register_and_unregister():
    sm = SystemsManager()
    a, b, c = DummySystem(), DummySystem(), DummySystem()

    sm.register(a)
    sm.register(b)
    sm.register(c)
    assert list(sm) == [a, b, c]

    sm.unregister(b)
    assert list(sm) == [a, c]


def test_update_calls_systems_in_order():
    sm = SystemsManager()
    a, b = DummySystem(), DummySystem()
    sm.register(a)
    sm.register(b)

    sm.update(42)
    assert a.calls == [42]
    assert b.calls == [42]
