from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.systems.ai.actions import ActionQueue
import logging

from agent_world.systems.ai.actions import (
    MoveAction,
    AttackAction,
    LogAction,
    IdleAction,
)
from agent_world.systems.ai.action_execution_system import ActionExecutionSystem
from agent_world.systems.movement.movement_system import Velocity
from agent_world.core.components.force import Force, apply_force


class DummyCombat:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, int]] = []

    def attack(self, attacker: int, target: int, tick: int | None = None) -> bool:
        self.calls.append((attacker, target, tick or 0))
        return True


def _make_world() -> World:
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    return w


def test_apply_force_accumulates() -> None:
    world = _make_world()
    e = world.entity_manager.create_entity()

    apply_force(world, e, 1.0, 0.5, ttl=2)
    apply_force(world, e, 0.5, -1.0)

    force = world.component_manager.get_component(e, Force)
    assert force is not None
    assert force.dx == 1.5
    assert force.dy == -0.5
    assert force.ttl == 2


def test_action_execution_translates_actions() -> None:
    world = _make_world()
    combat = DummyCombat()
    queue = ActionQueue()

    attacker = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    # start with a velocity component that should be removed
    world.component_manager.add_component(attacker, Velocity(1, 1))

    queue.enqueue_raw(attacker, "MOVE E")
    queue.enqueue_raw(attacker, f"ATTACK {target}")

    system = ActionExecutionSystem(world, queue, combat)
    system.update(tick=5)

    force = world.component_manager.get_component(attacker, Force)
    assert force is not None and (force.dx, force.dy) == (1, 0)
    assert world.component_manager.get_component(attacker, Velocity) is None
    assert combat.calls == [(attacker, target, 5)]


def test_log_and_idle_actions(capsys) -> None:
    world = _make_world()
    combat = DummyCombat()
    queue = ActionQueue()
    actor = world.entity_manager.create_entity()

    queue.enqueue_raw(actor, "LOG test")
    queue.enqueue_raw(actor, "IDLE")

    system = ActionExecutionSystem(world, queue, combat)
    system.update(tick=1)

    captured = capsys.readouterr().out
    assert "test" in captured
    assert combat.calls == []


def test_unknown_action_logs_warning(caplog) -> None:
    world = _make_world()
    combat = DummyCombat()
    queue = ActionQueue()

    class UnknownAction:
        def __init__(self) -> None:
            self.actor = 1

    queue._queue.append(UnknownAction())

    system = ActionExecutionSystem(world, queue, combat)
    with caplog.at_level(logging.WARNING):
        system.update(tick=1)
    assert any("Unknown action" in r.message for r in caplog.records)
