import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.systems.ai.actions import (
    parse_action,
    ActionQueue,
    MoveAction,
    AttackAction,
)


def test_parse_move_action():
    action = parse_action(1, "MOVE N")
    assert isinstance(action, MoveAction)
    assert (action.dx, action.dy) == (0, -1)
    assert action.actor == 1


def test_parse_attack_action():
    action = parse_action(2, "ATTACK 5")
    assert isinstance(action, AttackAction)
    assert action.actor == 2
    assert action.target == 5


def test_parse_invalid_action():
    assert parse_action(1, "JUMP") is None
    assert parse_action(1, "MOVE Z") is None
    assert parse_action(1, "ATTACK foo") is None


def test_action_queue_enqueues_valid_actions():
    q = ActionQueue()
    q.enqueue_raw(1, "MOVE E")
    q.enqueue_raw(1, "JUNK")
    assert len(q) == 1
    action = q.pop()
    assert isinstance(action, MoveAction)
    assert (action.dx, action.dy) == (1, 0)
