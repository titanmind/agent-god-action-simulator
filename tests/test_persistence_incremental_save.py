import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.persistence.save_load import save_world
from agent_world.persistence.incremental_save import (
    save_incremental,
    load_incremental,
)


def _make_world() -> World:
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    w.time_manager = TimeManager()
    return w


def test_save_and_load_incremental(tmp_path: Path) -> None:
    base_dir = tmp_path / "world_1"
    inc_dir = base_dir / "increments"
    base_dir.mkdir()

    world = _make_world()
    save_world(world, base_dir / "world_state.json.gz")

    tm = world.time_manager
    assert tm is not None

    tm.tick_counter = 5
    eid = world.entity_manager.create_entity()
    world.component_manager.add_component(eid, Position(1, 2))
    world.entity_manager._entity_components[eid]["Position"] = Position(1, 2)
    save_incremental(world, inc_dir)

    tm.tick_counter = 10
    world.component_manager.add_component(eid, Health(cur=5, max=10))
    world.entity_manager._entity_components[eid]["Health"] = Health(cur=5, max=10)
    save_incremental(world, inc_dir)

    snap = inc_dir / f"{tm.tick_counter:07d}.json.gz"
    loaded = load_incremental(snap)
    cm = loaded.component_manager
    assert cm.get_component(eid, Position) is not None
    hp = cm.get_component(eid, Health)
    assert hp is not None and hp.cur == 5
    assert loaded.time_manager.tick_counter == 10
