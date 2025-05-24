"""World bootstrap and minimal tick loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import threading
import time
import os

from dotenv import load_dotenv

import yaml

from .core.world import World
from .core.entity_manager import EntityManager
from .core.component_manager import ComponentManager
from .core.time_manager import TimeManager
from .systems.ai.actions import ActionQueue
from .core.systems_manager import SystemsManager
from .systems.movement.physics_system import PhysicsSystem
from .systems.movement.movement_system import MovementSystem
from .systems.perception.perception_system import PerceptionSystem
from .systems.combat.combat_system import CombatSystem
from .systems.interaction.pickup import PickupSystem
from .systems.interaction.trading import TradingSystem
from .systems.interaction.stealing import StealingSystem
from .systems.interaction.crafting import CraftingSystem
from .systems.ability.ability_system import AbilitySystem
from .systems.ai.ai_reasoning_system import AIReasoningSystem

try:  # Optional system may not exist yet
    from .systems.ai.action_execution_system import ActionExecutionSystem
except Exception:  # pragma: no cover - optional module
    ActionExecutionSystem = None  # type: ignore
from .ai.llm.llm_manager import LLMManager
from .persistence.save_load import load_world, save_world
from .persistence.incremental_save import start_incremental_save
from .utils.cli.command_parser import poll_command
from .utils.cli.commands import execute


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")
AUTO_SAVE_INTERVAL = 60.0  # seconds


def bootstrap(config_path: str | Path = Path("config.yaml")) -> World:
    """Create the core ``World`` instance and attach managers."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh) or {}

    world_cfg = cfg.get("world", {})
    size = tuple(world_cfg.get("size", [10, 10]))  # type: ignore[arg-type]
    tick_rate = float(world_cfg.get("tick_rate", 10))

    world = World(size)
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager(tick_rate)

    # ------------------------------------------------------------------
    # SYSTEMS WIRING: instantiate manager and core systems
    # ------------------------------------------------------------------
    world.systems_manager = SystemsManager()
    sm = world.systems_manager

    physics = PhysicsSystem(world)
    movement = MovementSystem(world)
    perception = PerceptionSystem(world)
    combat = CombatSystem(world)
    pickup = PickupSystem(world)
    trading = TradingSystem(world)
    stealing = StealingSystem(world)
    crafting = CraftingSystem(world)
    ability = AbilitySystem(world)

    llm = LLMManager()
    actions = ActionQueue()
    ai_reasoning = AIReasoningSystem(world, llm, actions)

    sm.register(physics)
    sm.register(movement)
    sm.register(perception)
    sm.register(combat)
    sm.register(pickup)
    sm.register(trading)
    sm.register(stealing)
    sm.register(crafting)
    sm.register(ability)
    sm.register(ai_reasoning)

    if ActionExecutionSystem is not None:
        sm.register(ActionExecutionSystem(world, actions, combat))

    # ------------------------------------------------------------------
    # END SYSTEMS WIRING
    # ------------------------------------------------------------------

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
    # PERSISTENCE HOOK: start incremental snapshots
    start_incremental_save(world, path.parent / "increments")


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
            if world.systems_manager:
                world.systems_manager.update(world, tm.tick_counter)
            tm.sleep_until_next_tick()
            step_once = False
        else:  # idle while paused
            time.sleep(0.01)


if __name__ == "__main__":
    main()
