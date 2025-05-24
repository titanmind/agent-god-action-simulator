
# agent_world/main.py
"""World bootstrap and minimal tick loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import threading
import time
import os
import asyncio

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
    ActionExecutionSystem = None

from .ai.llm.llm_manager import LLMManager
from .persistence.save_load import load_world, save_world
from .core.spatial.spatial_index import SpatialGrid
from .persistence.incremental_save import start_incremental_save
from .utils.cli.command_parser import poll_command, start_cli_thread, stop_cli_thread
from .utils.cli.commands import execute # `execute` is used for spawning
from .gui.renderer import Renderer
from .gui import input as gui_input
from .core.components.position import Position
from .core.components.health import Health
from .core.components.physics import Physics


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
    size = tuple(world_cfg.get("size", [100, 100])) # Increased default size
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
    world.gui_enabled = False

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

    player_pos = (size[0] // 2 - 5, size[1] // 2) # Slightly offset player for space
    world.component_manager.add_component(PLAYER_ID, Position(*player_pos))
    world.component_manager.add_component(PLAYER_ID, Health(cur=100,max=100))
    world.component_manager.add_component(PLAYER_ID, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
    world.spatial_index.insert(PLAYER_ID, player_pos)

    world.systems_manager = SystemsManager()
    sm = world.systems_manager
    physics = PhysicsSystem(world)
    movement = MovementSystem(world)
    perception_cfg = cfg.get("perception", {})
    view_radius = int(perception_cfg.get("view_radius", 10)) # Increased view radius
    perception = PerceptionSystem(world, view_radius=view_radius)
    combat_event_log: list[dict[str, Any]] = []
    combat = CombatSystem(world, event_log=combat_event_log)
    pickup = PickupSystem(world)
    trading = TradingSystem(world)
    stealing = StealingSystem(world)
    crafting_event_log: list[dict[str, Any]] = []
    crafting = CraftingSystem(world, event_log=crafting_event_log)
    ability = AbilitySystem(world)
    ai_reasoning = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor)

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
        action_execution_system_instance = ActionExecutionSystem(world, world.action_queue, combat)
        sm.register(action_execution_system_instance)

    # Generate some resources on the map
    world.generate_resources(seed=12345) # Use a fixed seed for predictable resources
    print(f"[Bootstrap] Generated resources on the map.")

    return world

# ... (load_or_bootstrap and start_autosave remain the same) ...

def main() -> None:
    pygame.init()
    pygame.font.init()

    world = load_or_bootstrap()

    if not all([world.time_manager, world.action_queue is not None,
                world.raw_actions_with_actor is not None, world.systems_manager,
                world.entity_manager, world.component_manager, world.spatial_index,
                world.llm_manager_instance]):
        print("Critical Error: World not properly initialized! Exiting.")
        if pygame.get_init(): pygame.quit()
        return

    autosave_thread = start_autosave(world)
    cli_input_thread = start_cli_thread()

    tm = world.time_manager
    actual_renderer = Renderer()

    world_center_x = world.size[0] / 2.0
    world_center_y = world.size[1] / 2.0
    actual_renderer.set_camera_center(world_center_x, world_center_y)
    print(f"Initial camera center set to: ({actual_renderer.camera_world_x}, {actual_renderer.camera_world_y})")

    # --- Spawn two NPCs ---
    initial_spawn_state = {"renderer": actual_renderer} # State for CLI command execution context
    # Spawn first NPC
    execute("spawn", ["npc", str(int(world_center_x)), str(int(world_center_y))], world, initial_spawn_state)
    # Spawn second NPC, slightly offset
    execute("spawn", ["npc", str(int(world_center_x + 3)), str(int(world_center_y + 2))], world, initial_spawn_state)
    # Spawn an item for interaction
    execute("spawn", ["item", str(int(world_center_x - 3)), str(int(world_center_y - 2))], world, initial_spawn_state)


    paused = False
    step_once = False
    running = True

    print("\nApplication started. CLI is active. Type /help for commands, or /gui to toggle display.")

    last_debug_print_time = time.time()
    clock = pygame.time.Clock()

    try:
        while running:
            gui_events_state = {
                "paused": paused, "running": running,
                "fps_enabled": world.fps_enabled, "renderer": actual_renderer
            }
            if world.gui_enabled and actual_renderer.window:
                gui_input.handle_events(world, actual_renderer, world.action_queue, gui_events_state)
            else: # Still pump events if GUI is off, to catch QUIT
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
            if not running: break


            paused = gui_events_state["paused"]
            # running = gui_events_state["running"] # running is handled by event loop
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
                running = cli_command_state["running"] # execute can set running to False
                if cli_command_state.get("step"): step_once = True
                world.gui_enabled = cli_command_state["gui_enabled"]
                world.fps_enabled = cli_command_state["fps_enabled"]
            if not running: break

            if not paused or step_once:
                if world.raw_actions_with_actor:
                    print(f"[Tick {tm.tick_counter}] MainLoop: Raw AI actions to process: {world.raw_actions_with_actor}")

                print(f"[Tick {tm.tick_counter}] MainLoop: world.action_queue IS {'NOT None' if world.action_queue is not None else 'None'}")

                if world.raw_actions_with_actor and world.action_queue is not None:
                    print(f"[Tick {tm.tick_counter}] MainLoop: Processing {len(world.raw_actions_with_actor)} raw actions into ActionQueue.")
                    for actor_id, action_text in world.raw_actions_with_actor:
                       world.action_queue.enqueue_raw(actor_id, action_text)
                    world.raw_actions_with_actor.clear()
                elif world.raw_actions_with_actor and world.action_queue is None:
                    print(f"[Tick {tm.tick_counter}] MainLoop: CRITICAL - world.action_queue is None, cannot process raw actions.")


                if world.action_queue and len(world.action_queue._queue) > 0:
                    print(f"[Tick {tm.tick_counter}] MainLoop: ActionQueue contents before exec: {list(world.action_queue._queue)}")

                if world.systems_manager:
                    world.systems_manager.update(world, tm.tick_counter)

                tm.sleep_until_next_tick() # This now calls renderer if GUI hook is active
                step_once = False
            else: # If paused and not stepping
                if world.gui_enabled and actual_renderer.window and hasattr(actual_renderer.window, '_surface'):
                    # Manually call render update if paused to keep GUI responsive for panning/zooming
                    actual_renderer.window.clear((10, 10, 10))
                    actual_renderer.update(world) # Draw world state
                    actual_renderer.window.refresh()
                else: # If no GUI or paused, just sleep a bit to not spin CPU
                    time.sleep(0.016) # Approx 60 FPS idle

            current_time = time.time()
            if current_time - last_debug_print_time >= 10.0:
                last_debug_print_time = current_time

            clock.tick(60) # Cap Pygame loop FPS, not simulation tick rate

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught. Shutting down...")
        running = False
    finally:
        print("Application shutting down...")
        stop_cli_thread()
        # autosave_thread is daemon, will exit.
        if cli_input_thread and cli_input_thread.is_alive():
             cli_input_thread.join(timeout=1.0)
        if pygame.get_init():
            pygame.quit()

if __name__ == "__main__":
    main()