
# agent-god-action-simulator/agent_world/main.py
"""World bootstrap and minimal tick loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import threading
import time
import os
import asyncio
from agent_world.ai.angel.generator import GENERATED_DIR as ABILITIES_GENERATED_DIR # Add this import
import shutil # Add this import

from dotenv import load_dotenv

import yaml
import pygame

from .core.world import World
from .core.entity_manager import EntityManager
from .core.component_manager import ComponentManager
from .core.time_manager import TimeManager
from .systems.ai.actions import ActionQueue, PLAYER_ID
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
from .core.components.health import Health
from .core.components.physics import Physics
from .core.components.ai_state import AIState # For goal setting in scenario
from .systems.movement.pathfinding import set_obstacles, clear_obstacles # For scenario obstacles


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")
AUTO_SAVE_INTERVAL = 60.0


def bootstrap(config_path: str | Path = Path("config.yaml")) -> World:
    env_path = Path(".env")
    if env_path.exists(): load_dotenv(env_path)

    actual_config_path = Path(config_path)
    cfg: dict[str, Any] = {}
    if actual_config_path.is_file():
        with open(actual_config_path, "r", encoding="utf-8") as fh: cfg = yaml.safe_load(fh) or {}
    else:
        project_root_config = Path(__file__).resolve().parents[1] / "config.yaml"
        if project_root_config.is_file():
            with open(project_root_config, "r", encoding="utf-8") as fh: cfg = yaml.safe_load(fh) or {}
        else:
            print(f"Warning: Config file '{config_path}' (and at project root) not found. Using defaults.")

    world_cfg = cfg.get("world", {})
    size = tuple(world_cfg.get("size", [100, 100]))
    tick_rate = float(world_cfg.get("tick_rate", 10))

    world = World(size)
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager(tick_rate)
    world.spatial_index = SpatialGrid(cell_size=1)

    world.action_queue = ActionQueue()
    print(f"[Bootstrap] world.action_queue initialized: {world.action_queue is not None}")
    world.raw_actions_with_actor = []
    world.fps_enabled = False
    world.gui_enabled = True # GUI enabled by default

    llm_cfg = cfg.get("llm", {})
    llm_api_key = os.getenv("OPENROUTER_API_KEY") or llm_cfg.get("api_key")
    llm_model = os.getenv("OPENROUTER_MODEL") or llm_cfg.get("model")
    llm = LLMManager(api_key=llm_api_key, model=llm_model)
    world.llm_manager_instance = llm
    if llm.mode == "live" and world.llm_manager_instance and not llm.offline:
        world.llm_manager_instance.start_processing_loop(world)

    if not world.entity_manager.has_entity(PLAYER_ID):
        if PLAYER_ID not in world.entity_manager._entity_components:
             world.entity_manager._entity_components[PLAYER_ID] = {}
             world.entity_manager._next_id = max(world.entity_manager._next_id, PLAYER_ID +1)

    player_pos = (size[0] // 2 - 5, size[1] // 2)
    world.component_manager.add_component(PLAYER_ID, Position(*player_pos))
    world.component_manager.add_component(PLAYER_ID, Health(cur=100,max=100))
    world.component_manager.add_component(PLAYER_ID, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
    world.spatial_index.insert(PLAYER_ID, player_pos)

    world.systems_manager = SystemsManager()
    sm = world.systems_manager
    physics_sys = PhysicsSystem(world) # Renamed to avoid conflict with Physics component
    movement_sys = MovementSystem(world) # Renamed
    perception_cfg = cfg.get("perception", {})
    view_radius = int(perception_cfg.get("view_radius", 10))
    perception_sys = PerceptionSystem(world, view_radius=view_radius) # Renamed
    combat_event_log: list[dict[str, Any]] = []
    combat_sys = CombatSystem(world, event_log=combat_event_log) # Renamed
    pickup_sys = PickupSystem(world) # Renamed
    trading_sys = TradingSystem(world) # Renamed
    stealing_sys = StealingSystem(world) # Renamed
    crafting_event_log: list[dict[str, Any]] = []
    crafting_sys = CraftingSystem(world, event_log=crafting_event_log) # Renamed
    ability_sys = AbilitySystem(world) # Renamed
    ai_reasoning_sys = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor) # Renamed

    sm.register(physics_sys)
    sm.register(movement_sys)
    sm.register(perception_sys)
    sm.register(combat_sys)
    sm.register(pickup_sys)
    sm.register(trading_sys)
    sm.register(stealing_sys)
    sm.register(crafting_sys)
    sm.register(ability_sys) # AbilitySystem needs to be registered
    world.ability_system_instance = ability_sys # Store instance on world
    sm.register(ai_reasoning_sys)

    if ActionExecutionSystem is not None:
        action_execution_system_instance = ActionExecutionSystem(world, world.action_queue, combat_sys)
        sm.register(action_execution_system_instance)
    else:
        print("[Bootstrap CRITICAL] ActionExecutionSystem is None after import attempt.")


    world.generate_resources(seed=12345)
    print(f"[Bootstrap] Generated resources on the map.")

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
        print(f"Save file found at {path}. Attempting to load state.")
        try:
            loaded_world_from_file = load_world(path)
            
            world_shell.entity_manager = loaded_world_from_file.entity_manager
            world_shell.component_manager = loaded_world_from_file.component_manager
            world_shell.tile_map = loaded_world_from_file.tile_map
            if loaded_world_from_file.time_manager:
                 world_shell.time_manager.tick_counter = loaded_world_from_file.time_manager.tick_counter
            if hasattr(loaded_world_from_file, 'gui_enabled'):
                world_shell.gui_enabled = loaded_world_from_file.gui_enabled
                print(f"[Load] GUI enabled state loaded from save: {world_shell.gui_enabled}")
            
            world_shell.spatial_index._cells.clear() 
            world_shell.spatial_index._entity_pos.clear()
            batch: list[tuple[int, tuple[int, int]]] = []
            if world_shell.entity_manager and world_shell.component_manager:
                for eid_int in list(world_shell.entity_manager.all_entities.keys()):
                    pos_comp = world_shell.component_manager.get_component(eid_int, Position) # Renamed var
                    if pos_comp is not None: batch.append((eid_int, (pos_comp.x, pos_comp.y)))
            if batch: world_shell.spatial_index.insert_many(batch)
            
            print(f"Successfully loaded state from {path} into world structure.")
            return world_shell
        except Exception as exc:
            print(f"Error loading world from {path}: {exc}. Using freshly bootstrapped world.")
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
            print(f"Error creating save directory {path.parent}: {e}. Auto-save disabled.")
            return None
    def _loop() -> None:
        while True:
            time.sleep(interval) 
            if not world.time_manager: continue 
            try: save_world(world, path)
            except Exception as exc: print(f"Auto-save failed: {exc}")
    t = threading.Thread(target=_loop, daemon=True, name="AutoSaveThread")
    t.start()
    inc_save_path = path.parent / "increments"
    if not inc_save_path.exists():
        try: inc_save_path.mkdir(parents=True, exist_ok=True)
        except OSError as e: print(f"Error creating incremental save directory {inc_save_path}: {e}.")
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
        print(f"[Main Init] Cleared old files from {ABILITIES_GENERATED_DIR}")
    # +++ END CLEAN +++
    pygame.init()
    pygame.font.init()

    # --- SCENARIO SETUP: Clear any persistent obstacles from previous runs ---
    clear_obstacles() # Clear obstacles at the start of each run for this scenario

    world = load_or_bootstrap()

    if not all([world.time_manager, world.action_queue is not None,
                world.raw_actions_with_actor is not None, world.systems_manager,
                world.entity_manager, world.component_manager, world.spatial_index,
                world.llm_manager_instance, world.ability_system_instance]): # Added ability_system_instance check
        print("Critical Error: World not properly initialized! Exiting.")
        if pygame.get_init(): pygame.quit()
        return

    autosave_thread = start_autosave(world)
    cli_input_thread = start_cli_thread()

    tm = world.time_manager
    actual_renderer = Renderer()
    # world.ability_system_instance is now set during bootstrap and load_or_bootstrap if AbilitySystem is registered.
    if not world.ability_system_instance:
        print("[Main WARNING] AbilitySystem instance not found on world object after bootstrap/load!")


    world_center_x = world.size[0] // 2
    world_center_y = world.size[1] // 2
    actual_renderer.set_camera_center(float(world_center_x), float(world_center_y))
    print(f"Initial camera center set to: ({actual_renderer.camera_world_x}, {actual_renderer.camera_world_y})")

    initial_spawn_state = {"renderer": actual_renderer} # For GUI updates during spawn

    # --- SCENARIO FOR ABILITY GENERATION & PICKUP (Goal 2.1) ---
    agent_start_x = world_center_x
    agent_start_y = world_center_y
    
    # Spawn agent who needs the item
    agent_id_scenario = execute("spawn", ["npc", str(agent_start_x), str(agent_start_y)], world, initial_spawn_state)
    
    item_target_x = agent_start_x
    item_target_y = agent_start_y - 2 
    item_id_scenario = execute("spawn", ["item", str(item_target_x), str(item_target_y)], world, initial_spawn_state)

    if agent_id_scenario and item_id_scenario and world.component_manager:
        ai_state_agent = world.component_manager.get_component(agent_id_scenario, AIState)
        if ai_state_agent:
            ai_state_agent.goals = [f"Acquire item {item_id_scenario}"] 
            print(f"[Scenario] Agent {agent_id_scenario} at ({agent_start_x},{agent_start_y}) given goal: {ai_state_agent.goals}")
        item_pos_comp = world.component_manager.get_component(item_id_scenario, Position)
        if item_pos_comp:
             print(f"[Scenario] Item {item_id_scenario} spawned at ({item_pos_comp.x},{item_pos_comp.y}) for Agent {agent_id_scenario}.")
        else:
             print(f"[Scenario WARNING] Item {item_id_scenario} spawned but has no Position component!")

    obstacle_pos = (agent_start_x, agent_start_y - 1) # Between agent and item
    set_obstacles([obstacle_pos])
    print(f"[Scenario] Obstacle placed at {obstacle_pos}")
    # --- END SCENARIO ---

    # +++ ADD THIS DEBUG BLOCK in main() +++
    print(f" agent id scenario: {agent_id_scenario}")
    print(f" world component manager: {world.component_manager}")
    if agent_id_scenario and world.component_manager:
        final_check_ai_state = world.component_manager.get_component(agent_id_scenario, AIState)
        if final_check_ai_state:
            print(f"[[[[[ PRE-LOOP CHECK (main.py) Agent {agent_id_scenario} AIState ID: {id(final_check_ai_state)}, Goals: {final_check_ai_state.goals} ]]]]]")
        else:
            print(f"[[[[[ PRE-LOOP CHECK (main.py) Agent {agent_id_scenario} AIState NOT FOUND ]]]]]")
    # +++ END DEBUG BLOCK +++


    if world.gui_enabled and actual_renderer:
        install_gui_rendering_hook(world, actual_renderer)
        print("[Main] GUI rendering hook installed on startup as world.gui_enabled is True.")

    paused = False
    step_once = False
    running = True

    print("\nApplication started. CLI is active. Type /help for commands, or /gui to toggle display.")

    # last_debug_print_time = time.time() # Keep if needed for other debug
    clock = pygame.time.Clock()

    try:
        while running:
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
                if world.raw_actions_with_actor and world.action_queue is not None:
                    for actor_id, action_text in world.raw_actions_with_actor:
                       world.action_queue.enqueue_raw(actor_id, action_text)
                    world.raw_actions_with_actor.clear()
                elif world.raw_actions_with_actor and world.action_queue is None:
                    print(f"[Tick {tm.tick_counter}] MainLoop: CRITICAL - world.action_queue is None.")

                if not world.paused_for_angel:
                    if world.systems_manager:
                        world.systems_manager.update(world, tm.tick_counter) # Pass world and tick

                    tm.sleep_until_next_tick()
                else:
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
        print("\nKeyboardInterrupt caught. Shutting down...")
        running = False
    finally:
        print("Application shutting down...")
        stop_cli_thread()
        if cli_input_thread and cli_input_thread.is_alive():
             cli_input_thread.join(timeout=1.0)
        if pygame.get_init():
            pygame.quit()
        clear_obstacles() # Clean up obstacles for next run

if __name__ == "__main__":
    main()