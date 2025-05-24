import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.ai.memory import ShortTermMemory


def test_store_and_retrieve_order():
    mem = ShortTermMemory(capacity=3)
    mem.store(1, "a")
    mem.store(1, "b")
    mem.store(1, "c")
    assert mem.retrieve(1, 2) == ["c", "b"]


def test_prune_on_overflow():
    mem = ShortTermMemory(capacity=2)
    mem.store(1, "a")
    mem.store(1, "b")
    mem.store(1, "c")
    assert mem.retrieve(1, 3) == ["c", "b"]


def test_isolation_between_agents():
    mem = ShortTermMemory(capacity=5)
    mem.store(1, "a1")
    mem.store(2, "b1")
    mem.store(1, "a2")
    assert mem.retrieve(1, 2) == ["a2", "a1"]
    assert mem.retrieve(2, 1) == ["b1"]
