"""World bootstrap and minimal tick loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .core.world import World
from .core.entity_manager import EntityManager
from .core.component_manager import ComponentManager
from .core.time_manager import TimeManager


def bootstrap(config_path: str | Path = Path("config.yaml")) -> World:
    """Create the core ``World`` instance and attach managers."""

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh) or {}

    world_cfg = cfg.get("world", {})
    size = tuple(world_cfg.get("size", [10, 10]))  # type: ignore[arg-type]
    tick_rate = float(world_cfg.get("tick_rate", 10))

    world = World(size)
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager(tick_rate)
    # Systems manager will be implemented later; placeholder list for now
    world.systems_manager = []

    return world


def main() -> None:
    """Run a short dummy loop to verify bootstrapping."""

    world = bootstrap()
    tm = world.time_manager
    assert tm is not None
    for _ in range(10):
        print(f"tick {tm.tick_counter}")
        tm.sleep_until_next_tick()


if __name__ == "__main__":
    main()

