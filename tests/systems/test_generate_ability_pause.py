from pathlib import Path

from agent_world.core.world import World
from agent_world.systems.ai.actions import ActionQueue, GenerateAbilityAction
from agent_world.systems.ai.action_execution_system import ActionExecutionSystem
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.ai.angel import generator as angel_generator


def test_pause_flag_set_and_cleared(monkeypatch):
    world = World((5, 5))
    world.component_manager = object()
    queue = ActionQueue()
    combat = CombatSystem(world)
    system = ActionExecutionSystem(world, queue, combat)

    called = {}

    def stub_generate(desc: str):
        called["during"] = world.paused_for_angel
        assert world.paused_for_angel is True
        return Path("dummy.py")

    monkeypatch.setattr(angel_generator, "generate_ability", stub_generate)

    queue._queue.append(GenerateAbilityAction(actor=1, description="test"))
    assert world.paused_for_angel is False
    system.update(0)
    assert called.get("during") is True
    assert world.paused_for_angel is False


def test_pause_flag_reset_on_exception(monkeypatch):
    world = World((5, 5))
    world.component_manager = object()
    queue = ActionQueue()
    combat = CombatSystem(world)
    system = ActionExecutionSystem(world, queue, combat)

    def stub_generate(desc: str):
        assert world.paused_for_angel is True
        raise RuntimeError("boom")

    monkeypatch.setattr(angel_generator, "generate_ability", stub_generate)

    queue._queue.append(GenerateAbilityAction(actor=2, description="oops"))
    system.update(1)
    assert world.paused_for_angel is False
