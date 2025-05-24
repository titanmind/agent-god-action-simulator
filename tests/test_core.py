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
