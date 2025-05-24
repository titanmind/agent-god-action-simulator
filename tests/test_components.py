import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.core.components.inventory import Inventory


def test_position_dataclass():
    p = Position(1, 2)
    assert (p.x, p.y) == (1, 2)


def test_health_dataclass():
    h = Health(5, 10)
    assert h.cur == 5
    assert h.max == 10


def test_inventory_defaults():
    inv1 = Inventory(capacity=2)
    inv2 = Inventory(capacity=3)
    assert inv1.capacity == 2
    assert inv1.items == []
    assert inv2.items == []
    assert inv1.items is not inv2.items
