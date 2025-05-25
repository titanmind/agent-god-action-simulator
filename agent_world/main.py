# agent-god-action-simulator/agent_world/main.py
"""World bootstrap and minimal tick loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import threading
import time
import os
import asyncio
import logging
from agent_world.ai.angel.generator import GENERATED_DIR as ABILITIES_GENERATED_DIR # Add this import
import shutil # Add this import

from dotenv import load_dotenv

from .config import load_config, CONFIG
import pygame

from .core.world import World
from .core.entity_manager import EntityManager
from .core.component_manager import ComponentManager
from .core.time_manager import TimeManager
from .systems.ai.actions import ActionQueue
from .core.systems_manager import SystemsManager
from .systems.movement.physics_system import PhysicsSystem
from .systems.movement.movement_system import MovementSystem
from .systems.perception.perception_system import PerceptionSystem as VisibilityPerceptionSystem
# Line 30: Corrected import
from .systems.ai.perception_system import EventPerceptionSystem
from .systems.combat.combat_system import CombatSystem
from .systems.interaction.pickup import PickupSystem
from .systems.interaction.trading import TradingSystem
from .systems.interaction.stealing import StealingSystem
from .systems.interaction.crafting import CraftingSystem
from .systems.ability.ability_system import AbilitySystem
from .systems.ai.ai_reasoning_system import AIReasoningSystem, RawActionCollector
from .systems.ai.behavior_tree_system import BehaviorTreeSystem
from .ai.behaviors.creature_bt import build_creature_tree
from .ai.angel.system import get_angel_system

try:
    from .systems.ai.action_execution_system import ActionExecutionSystem
except ImportError:
    ActionExecutionSystem = None # Should not happen with correct file structure

from .ai.llm.llm_manager import LLMManager
from .persistence.save_load import load_world, save_world
from .core.spatial.spatial_index import SpatialGrid
from .persistence.incremental_save import start_incremental_save
from .utils.cli.command_parser import poll_command, start_cli_thread, stop_cli_thread
from .utils.cli.commands import execute, _install_gui_hook as install_gui_rendering_hook
from .gui.renderer import Renderer
from .gui import input as gui_input
from .core.components.position import Position
from .systems.movement.pathfinding import clear_obstacles  # For scenario obstacles
from .scenarios.default_pickup_scenario import DefaultPickupScenario


log_level_str = CONFIG.logging.global_level
numeric_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__) # For main.py specific logs

# Apply per-module levels if defined
if CONFIG.logging.module_levels:
    for module_name, level_str in CONFIG.logging.module_levels.items():
        module_numeric_level = getattr(logging, level_str.upper(), None)
        if module_numeric_level is not None:
            logging.getLogger(module_name).setLevel(module_numeric_level)
        else:
            logger.warning("Invalid log level '%s' for module '%s' in config.", level_str, module_name)

DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")
AUTO_SAVE_INTERVAL = 60.0


def bootstrap(config_path: str | Path = Path("config.yaml")) -> World:
    env_path = Path(".env")
    if env_path.exists(): load_dotenv(env_path)

    actual_config_path = Path(config_path)
    cfg = load_config(actual_config_path)

    size = cfg.world.size
    tick_rate = cfg.world.tick_rate
    paused_timeout = cfg.world.paused_for_angel_timeout_seconds

    world = World(size)
    world.paused_for_angel_timeout_seconds = paused_timeout
    logger.info("[Bootstrap] Angel pause timeout set to %ss", paused_timeout)
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager(tick_rate)
    world.spatial_index = SpatialGrid(cell_size=1)

    world.action_queue = ActionQueue()
    logger.info("[Bootstrap] world.action_queue initialized: %s", world.action_queue is not None)
    world.raw_actions_with_actor = RawActionCollector(world.action_queue)
    world.fps_enabled = False
    world.gui_enabled = True # GUI enabled by default

    llm_api_key = os.getenv("OPENROUTER_API_KEY")
    llm_model = os.getenv("OPENROUTER_MODEL")
    llm = LLMManager(
        api_key=llm_api_key,
        model=llm_model,
        llm_config=cfg.llm,
    )
    logger.info(
        "[Bootstrap] LLM decision model: %s, Angel model: %s",
        llm.agent_decision_model,
        llm.angel_generation_model,
    )

    paths_cfg = cfg.paths
    if paths_cfg:
        world.paths = paths_cfg
        logger.info("[Bootstrap] Custom paths configuration loaded")
    world.llm_manager_instance = llm
    if llm.mode == "live" and world.llm_manager_instance and not llm.offline:
        world.llm_manager_instance.start_processing_loop(world)


    world.systems_manager = SystemsManager()
    sm = world.systems_manager
    physics_sys = PhysicsSystem(world) # Renamed to avoid conflict with Physics component
    movement_sys = MovementSystem(world) # Renamed
    perception_cfg = getattr(cfg, "perception", {}) or {}
    view_radius = int(perception_cfg.get("view_radius", 10))
    perception_sys = VisibilityPerceptionSystem(world, view_radius=view_radius)
    event_perception_sys = EventPerceptionSystem(world)
    combat_sys = CombatSystem(world)  # Renamed
    pickup_sys = PickupSystem(world) # Renamed
    trading_sys = TradingSystem(world) # Renamed
    stealing_sys = StealingSystem(world) # Renamed
    crafting_sys = CraftingSystem(world)  # Renamed
    ability_sys = AbilitySystem(world) # Renamed
    ai_reasoning_sys = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor) # Renamed

    sm.register(physics_sys)
    sm.register(movement_sys)
    behavior_tree_system = BehaviorTreeSystem(world)
    behavior_tree_system.register_tree("creature", build_creature_tree())
    sm.register(behavior_tree_system)
    world.behavior_tree_system_instance = behavior_tree_system
    sm.register(perception_sys)
    sm.register(event_perception_sys)
    sm.register(combat_sys)
    world.combat_system_instance = combat_sys
    sm.register(pickup_sys)
    sm.register(trading_sys)
    sm.register(stealing_sys)
    sm.register(crafting_sys)
    sm.register(ability_sys) # AbilitySystem needs to be registered
    if not hasattr(world, "ability_system_instance"):
        world.ability_system_instance = ability_sys
    angel_system = get_angel_system(world)
    sm.register(angel_system)
    sm.register(ai_reasoning_sys)

    if ActionExecutionSystem is not None:
        action_execution_system_instance = ActionExecutionSystem(world, world.action_queue, combat_sys)
        sm.register(action_execution_system_instance)
    else:
        logger.critical("[Bootstrap] ActionExecutionSystem is None after import attempt.")


    world.generate_resources(seed=12345)
    logger.info("[Bootstrap] Generated resources on the map.")

    return world


def load_or_bootstrap(
    save_path: str | Path = DEFAULT_SAVE_PATH,
    config_path: str | Path = Path("config.yaml"),
) -> World:
    path = Path(save_path)
    actual_config_path = Path(config_path)
    if not actual_config_path.is_file():
        project_root_config = Path(__file__).resolve().parents[1] / "config.yaml"
        if project_root_config.is_file(): actual_config_path = project_root_config
    
    world_shell = bootstrap(actual_config_path) 

    if path.is_file():
        logger.info("Save file found at %s. Attempting to load state.", path)
        try:
            loaded_world_from_file = load_world(path)
            
            world_shell.entity_manager = loaded_world_from_file.entity_manager
            world_shell.component_manager = loaded_world_from_file.component_manager
            world_shell.tile_map = loaded_world_from_file.tile_map
            if loaded_world_from_file.time_manager:
                 world_shell.time_manager.tick_counter = loaded_world_from_file.time_manager.tick_counter
            if hasattr(loaded_world_from_file, 'gui_enabled'):
                world_shell.gui_enabled = loaded_world_from_file.gui_enabled
                logger.info("[Load] GUI enabled state loaded from save: %s", world_shell.gui_enabled)
            
            world_shell.spatial_index._cells.clear() 
            world_shell.spatial_index._entity_pos.clear()
            batch: list[tuple[int, tuple[int, int]]] = []
            if world_shell.entity_manager and world_shell.component_manager:
                for eid_int in list(world_shell.entity_manager.all_entities.keys()):
                    pos_comp = world_shell.component_manager.get_component(eid_int, Position) # Renamed var
                    if pos_comp is not None: batch.append((eid_int, (pos_comp.x, pos_comp.y)))
            if batch: world_shell.spatial_index.insert_many(batch)
            
            logger.info("Successfully loaded state from %s into world structure.", path)
            return world_shell
        except Exception as exc:
            logger.error("Error loading world from %s: %s. Using freshly bootstrapped world.", path, exc)
            return world_shell
    else:
        return world_shell

def start_autosave(
    world: World,
    save_path: str | Path = DEFAULT_SAVE_PATH,
    interval: float = AUTO_SAVE_INTERVAL,
) -> threading.Thread | None:
    path = Path(save_path)
    if not path.parent.exists():
        try: path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Error creating save directory %s: %s. Auto-save disabled.", path.parent, e)
            return None
    def _loop() -> None:
        while True:
            time.sleep(interval) 
            if not world.time_manager: continue 
            try:
                save_world(world, path)
            except Exception as exc:
                logger.error("Auto-save failed: %s", exc)
    t = threading.Thread(target=_loop, daemon=True, name="AutoSaveThread")
    t.start()
    inc_save_path = path.parent / "increments"
    if not inc_save_path.exists():
        try: inc_save_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Error creating incremental save directory %s: %s.", inc_save_path, e)
    else:
        start_incremental_save(world, inc_save_path) 
    return t


def main() -> None:
    # +++ CLEAN GENERATED ABILITIES +++
    if ABILITIES_GENERATED_DIR.exists():
        for item in ABILITIES_GENERATED_DIR.iterdir():
            if item.name != "__init__.py": # Don't delete __init__.py
                if item.is_file():
                    item.unlink()
                elif item.is_dir(): # Should not happen, but good to be robust
                    shutil.rmtree(item)
        logger.info("[Main Init] Cleared old files from %s", ABILITIES_GENERATED_DIR)
    # +++ END CLEAN +++
    pygame.init()
    pygame.font.init()

    # --- SCENARIO SETUP: Clear any persistent obstacles from previous runs ---
    clear_obstacles()  # Clear obstacles at the start of each run for this scenario

    world = load_or_bootstrap()

    if not all([world.time_manager, world.action_queue is not None,
                world.raw_actions_with_actor is not None, world.systems_manager,
                world.entity_manager, world.component_manager, world.spatial_index,
                world.llm_manager_instance, world.ability_system_instance]): # Added ability_system_instance check
        logger.error("Critical Error: World not properly initialized! Exiting.")
        if pygame.get_init(): pygame.quit()
        return

    autosave_thread = start_autosave(world)
    cli_input_thread = start_cli_thread()

    tm = world.time_manager
    actual_renderer = Renderer()
    # world.ability_system_instance is now set during bootstrap and load_or_bootstrap if AbilitySystem is registered.
    if not world.ability_system_instance:
        logger.warning("[Main] AbilitySystem instance not found on world object after bootstrap/load!")


    world_center_x = world.size[0] // 2
    world_center_y = world.size[1] // 2
    actual_renderer.set_camera_center(float(world_center_x), float(world_center_y))
    logger.info(
        "Initial camera center set to: (%s, %s)",
        actual_renderer.camera_world_x,
        actual_renderer.camera_world_y,
    )

    # Run the default scenario if none specified via CLI
    DefaultPickupScenario().setup(world)


    if world.gui_enabled and actual_renderer:
        install_gui_rendering_hook(world, actual_renderer)
        logger.info("[Main] GUI rendering hook installed on startup as world.gui_enabled is True.")

    paused = False
    step_once = False
    running = True
    angel_pause_start: float | None = None

    logger.info("Application started. CLI is active. Type /help for commands, or /gui to toggle display.")

    # last_debug_print_time = time.time() # Keep if needed for other debug
    clock = pygame.time.Clock()

    try:
        while running:
            if world.paused_for_angel:
                if angel_pause_start is None:
                    angel_pause_start = time.time()
                elif (
                    world.paused_for_angel_timeout_seconds > 0
                    and time.time() - angel_pause_start
                    > world.paused_for_angel_timeout_seconds
                ):
                    logger.warning(
                        "[Main] Angel pause exceeded %ss; resuming.",
                        world.paused_for_angel_timeout_seconds,
                    )
                    world.paused_for_angel = False
                    angel_pause_start = None
            else:
                angel_pause_start = None
            gui_events_state = {
                "paused": paused, "running": running,
                "fps_enabled": world.fps_enabled, "renderer": actual_renderer
            }
            if world.gui_enabled and actual_renderer.window:
                gui_input.handle_events(world, actual_renderer, world.action_queue, gui_events_state)
            else: 
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
            if not running: break

            paused = gui_events_state["paused"]
            world.fps_enabled = gui_events_state["fps_enabled"]

            cli_command_state = {
                "paused": paused, "step": False, "gui_enabled": world.gui_enabled,
                "renderer": actual_renderer, "running": running,
                "fps_enabled": world.fps_enabled
            }
            cmd = poll_command()
            if cmd:
                execute(cmd.name, cmd.args, world, cli_command_state)
                paused = cli_command_state["paused"]
                running = cli_command_state["running"] 
                if cli_command_state.get("step"): step_once = True
                world.fps_enabled = cli_command_state["fps_enabled"]
            if not running: break

            if not paused or step_once:
                if not world.paused_for_angel:
                    if world.systems_manager:
                        world.systems_manager.update(world, tm.tick_counter) # Pass world and tick

                    tm.sleep_until_next_tick()
                else:
                    if getattr(world, "angel_system_instance", None):
                        world.angel_system_instance.process_pending_requests()
                    time.sleep(0.016)

                step_once = False
            else: 
                if world.gui_enabled and actual_renderer.window and hasattr(actual_renderer.window, '_surface'):
                    actual_renderer.window.clear((10, 10, 10))
                    actual_renderer.update(world) 
                    actual_renderer.window.refresh()
                else: 
                    time.sleep(0.016) 
            
            clock.tick(60)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt caught. Shutting down...")
        running = False
    finally:
        logger.info("Application shutting down...")
        stop_cli_thread()
        if cli_input_thread and cli_input_thread.is_alive():
             cli_input_thread.join(timeout=1.0)
        if pygame.get_init():
            pygame.quit()
        clear_obstacles() # Clean up obstacles for next run

if __name__ == "__main__":
    main()