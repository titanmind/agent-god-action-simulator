import time
from agent_world.main import bootstrap
from agent_world.core.world import World
from agent_world.ai.angel.system import AngelSystem, get_angel_system
from agent_world.systems.ai.actions import ActionQueue, GenerateAbilityAction
from agent_world.systems.ai.action_execution_system import ActionExecutionSystem
from agent_world.systems.combat.combat_system import CombatSystem


def test_angel_system_registered_and_process_called(monkeypatch):
    world = bootstrap(config_path="config.yaml")
    assert isinstance(world.angel_system_instance, AngelSystem)
    assert world.angel_system_instance in list(world.systems_manager)

    called = {}

    def fake_process() -> None:
        called["processed"] = True

    monkeypatch.setattr(world.angel_system_instance, "process_pending_requests", fake_process)
    world.paused_for_angel = True
    tm = world.time_manager
    tm.tick_counter = 0

    if not world.paused_for_angel:
        if world.systems_manager:
            world.systems_manager.update(world, tm.tick_counter)
        tm.sleep_until_next_tick()
    else:
        world.angel_system_instance.process_pending_requests()

    assert called.get("processed") is True


def test_generate_ability_action_queues(monkeypatch):
    world = World((5, 5))
    world.component_manager = object()
    queue = ActionQueue()
    combat = CombatSystem(world)
    system = ActionExecutionSystem(world, queue, combat)
    angel = get_angel_system(world)

    monkeypatch.setattr(angel, "generate_and_grant", lambda a, d: {"status": "stub"})
    captured = {}
    orig_queue = angel.queue_request

    def spy_queue(actor: int, desc: str):
        captured["actor"] = actor
        captured["desc"] = desc
        return orig_queue(actor, desc)

    monkeypatch.setattr(angel, "queue_request", spy_queue)

    queue._queue.append(GenerateAbilityAction(actor=1, description="test"))
    system.update(0)

    assert captured == {"actor": 1, "desc": "test"}
    assert (1, "test") in angel.request_queue
    assert world.paused_for_angel is False
