import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.core.world import World


def test_world_init_tile_map():
    w = World((3, 4))
    assert len(w.tile_map) == 4
    assert all(len(row) == 3 for row in w.tile_map)


def test_world_stub_methods():
    w = World((1, 1))
    # Should not raise
    w.add_entity(1)
    w.remove_entity(1)
    w.register_system(object())
    w.unregister_system(object())


def test_spawn_resource_populates_tile() -> None:
    w = World((5, 5))
    w.spawn_resource("ore", 2, 3)
    assert w.tile_map[3][2]["kind"] == "ore"


def test_generate_resources_deterministic() -> None:
    w1 = World((4, 4))
    w1.generate_resources(seed=123)
    w2 = World((4, 4))
    w2.generate_resources(seed=123)
    assert w1.tile_map == w2.tile_map
