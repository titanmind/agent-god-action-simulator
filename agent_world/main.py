"""World bootstrap and minimal tick loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import threading
import time

import yaml

from .core.world import World
from .core.entity_manager import EntityManager
from .core.component_manager import ComponentManager
from .core.time_manager import TimeManager
from .systems.ai.actions import ActionQueue
from .persistence.save_load import load_world, save_world
from .utils.cli.command_parser import poll_command
from .utils.cli.commands import execute


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")
AUTO_SAVE_INTERVAL = 60.0  # seconds


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


def load_or_bootstrap(
    save_path: str | Path = DEFAULT_SAVE_PATH,
    config_path: str | Path = Path("config.yaml"),
) -> World:
    """Load the world from ``save_path`` if present, else call :func:`bootstrap`."""

    path = Path(save_path)
    if path.exists():
        try:
            world = load_world(path)
        except Exception as exc:  # pragma: no cover - load failure fallback
            print(f"Failed to load world: {exc}. Bootstrapping new world.")
            return bootstrap(config_path)

        # Apply tick rate from config if present
        with open(config_path, "r", encoding="utf-8") as fh:
            cfg: dict[str, Any] = yaml.safe_load(fh) or {}
        tick_rate = float(cfg.get("world", {}).get("tick_rate", 10))
        if world.time_manager is None:
            world.time_manager = TimeManager(tick_rate)
        else:
            world.time_manager.tick_rate = tick_rate
        return world

    return bootstrap(config_path)


def start_autosave(
    world: World,
    save_path: str | Path = DEFAULT_SAVE_PATH,
    interval: float = AUTO_SAVE_INTERVAL,
) -> None:
    """Start a daemon thread that periodically saves ``world`` to ``save_path``."""

    path = Path(save_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    def _loop() -> None:
        while True:
            time.sleep(interval)
            try:
                save_world(world, path)
            except Exception as exc:  # pragma: no cover - background errors
                print(f"Auto-save failed: {exc}")

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def main() -> None:
    """Run a short dummy loop to verify bootstrapping."""

    world = load_or_bootstrap()
    start_autosave(world)
    tm = world.time_manager
    actions = ActionQueue()  # AI HOOK: queue for parsed actions
    assert tm is not None
    paused = False
    step_once = False
    for _ in range(10):
        cmd = poll_command()
        if cmd:
            state = {"paused": paused, "step": False}
            execute(cmd.name, cmd.args, world, state)
            paused = state["paused"]
            step_once = state.get("step", False) or step_once
        if not paused or step_once:
            print(f"tick {tm.tick_counter}")
            tm.sleep_until_next_tick()
            step_once = False
        else:  # idle while paused
            time.sleep(0.01)


if __name__ == "__main__":
    main()
