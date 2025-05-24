
"""Implementations of development CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, TYPE_CHECKING

from ...core.components.position import Position # For PLAYER_ID check in spawn
from ...core.components.health import Health
from ...core.components.inventory import Inventory
from ...systems.interaction.pickup import Tag 
from ...systems.ai.actions import PLAYER_ID # Import PLAYER_ID

from ...persistence.save_load import save_world
from ..observer import install_tick_observer, toggle_live_fps, print_fps as observer_print_fps 

if TYPE_CHECKING:
    from ...gui.renderer import Renderer 

try:
    from ..profiling import profile_ticks
except ImportError:
    def profile_ticks(n: int, tick_callback: Any, out_path: Any) -> None:
        print(f"Profiling (stub): {n} ticks, output to {out_path}")
        pass


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")


def pause(state: Dict[str, Any]) -> None:
    state["paused"] = True
    print("Simulation paused.")


def step(state: Dict[str, Any]) -> None:
    if state.get("paused", False):
        state["step"] = True
        print("Stepping one tick.")
    else:
        print("Simulation is not paused. Use /pause first.")


def save(world: Any, path: str | Path | None = None) -> None:
    save_path = Path(path) if path is not None else DEFAULT_SAVE_PATH
    try:
        save_world(world, save_path)
        print(f"World saved to {save_path}")
    except Exception as e:
        print(f"Error saving world: {e}")


def reload_abilities(world: Any) -> None:
    sm: Iterable[Any] | None = getattr(world, "systems_manager", None)
    if sm is None:
        print("SystemsManager not found in world.")
        return
    reloaded_count = 0
    for system in sm:
        if hasattr(system, "abilities") and hasattr(system, "_load_all"): 
            load_all_method = getattr(system, "_load_all", None) 
            if callable(load_all_method):
                try:
                    load_all_method()
                    reloaded_count +=1
                except Exception as e:
                    print(f"Error reloading abilities in system {type(system).__name__}: {e}")
    if reloaded_count > 0: print(f"Abilities reloaded for {reloaded_count} system(s).")
    else: print("No ability systems found or reloaded.")


def profile(world: Any, ticks_str: str | None = None) -> None:
    try:
        num_ticks = int(ticks_str) if ticks_str else 100 
        if num_ticks <=0:
            print("Number of ticks must be positive.")
            return
    except ValueError:
        print(f"Invalid number of ticks: {ticks_str}")
        return
    out_path = Path("profile.prof")
    print(f"Starting profiling for {num_ticks} ticks. Output to {out_path}")
    tm = getattr(world, "time_manager")
    sm = getattr(world, "systems_manager")
    aq = getattr(world, "action_queue")
    raw_aq = getattr(world, "raw_actions_with_actor")
    def single_world_tick_for_profiling():
        if raw_aq and aq:
            for actor_id, action_text in raw_aq: aq.enqueue_raw(actor_id, action_text)
            raw_aq.clear()
        if sm and tm:
            sm.update(world, tm.tick_counter)
            tm.tick_counter += 1 
    if not (tm and sm and aq is not None and raw_aq is not None):
        print("World components missing for profiling callback setup.")
        return
    try:
        profile_ticks(num_ticks, single_world_tick_for_profiling, out_path)
        print(f"Profiling complete. Stats saved to {out_path}")
    except Exception as e:
        print(f"Error during profiling: {e}")


def spawn(world: Any, kind: str, x_str: str | None = None, y_str: str | None = None) -> int | None:
    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    spatial_index = getattr(world, "spatial_index", None)
    if em is None or cm is None or spatial_index is None:
        print("World managers not initialized for spawn.")
        return None
    try:
        x = int(x_str) if x_str and x_str.lstrip('-').isdigit() else (world.size[0] // 2 if hasattr(world, 'size') else 0) # Default to center or 0
        y = int(y_str) if y_str and y_str.lstrip('-').isdigit() else (world.size[1] // 2 if hasattr(world, 'size') else 0)
    except ValueError:
        print("Invalid coordinates for spawn. Using defaults.")
        x = world.size[0] // 2 if hasattr(world, 'size') else 0
        y = world.size[1] // 2 if hasattr(world, 'size') else 0
    ent_id = em.create_entity()
    cm.add_component(ent_id, Position(x, y)) 
    kind_lower = kind.lower()
    if kind_lower == "npc":
        cm.add_component(ent_id, Health(cur=10, max=10))
        cm.add_component(ent_id, Inventory(capacity=4))
        print(f"Spawned NPC (ID: {ent_id}) at ({x},{y})")
    elif kind_lower == "item":
        cm.add_component(ent_id, Tag("item")) 
        print(f"Spawned Item (ID: {ent_id}) at ({x},{y})")
    else:
        em.destroy_entity(ent_id) 
        print(f"Unknown entity kind for spawn: '{kind}'. Known: npc, item.")
        return None
    spatial_index.insert(ent_id, (x, y))
    # Ensure player (ID 0) also has position if actions depend on it
    # This should ideally be handled in bootstrap more reliably
    if cm and not cm.get_component(PLAYER_ID, Position) and em.has_entity(PLAYER_ID):
        default_player_pos = (world.size[0] // 2, world.size[1] // 2) if hasattr(world, 'size') else (0,0)
        cm.add_component(PLAYER_ID, Position(*default_player_pos))
        spatial_index.insert(PLAYER_ID, default_player_pos)
        print(f"PLAYER_ID ({PLAYER_ID}) Position component added at {default_player_pos}.")
    return ent_id


def debug(world: Any, entity_id_str: str | None) -> None:
    if entity_id_str is None: print("Usage: /debug <entity_id>"); return
    try: entity_id = int(entity_id_str)
    except ValueError: print(f"Invalid entity id: {entity_id_str}"); return
    em = getattr(world, "entity_manager", None); cm = getattr(world, "component_manager", None)
    if em is None or cm is None: print("World managers not initialized for debug."); return
    if not em.has_entity(entity_id): print(f"Entity {entity_id} not found."); return
    entity_component_map = cm._components.get(entity_id) 
    print(f"--- Entity {entity_id} Components ---")
    if entity_component_map:
        for name, comp_instance in entity_component_map.items(): print(f"  {name}: {comp_instance}")
    else: print("  No components found for this entity."); 
    print("-----------------------------")


def fps(world: Any, state: Dict[str, Any]) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is not None: install_tick_observer(tm) 
    fps_is_now_enabled = toggle_live_fps()
    state["fps_enabled"] = fps_is_now_enabled 
    world.fps_enabled = fps_is_now_enabled 
    if fps_is_now_enabled: print("Live FPS display enabled."); observer_print_fps() 
    else: print("Live FPS display disabled.")


def _install_gui_hook(world: Any, renderer_instance: Renderer) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None: print("TimeManager not found. Cannot install GUI hook."); return
    if getattr(tm, "_gui_renderer_hook_instance", None) == renderer_instance: return
    if not hasattr(tm, "_original_sleep_method_gui"):
        tm._original_sleep_method_gui = tm.sleep_until_next_tick
    original_sleep = tm._original_sleep_method_gui

    def gui_rendering_sleep_wrapper() -> None:
        if getattr(world, "gui_enabled", False) and renderer_instance and renderer_instance.window:
            # print(f"Hook: GUI Enabled, Tick: {tm.tick_counter if tm else 'N/A'}") # DEBUG
            renderer_instance.window.clear((30, 30, 30)) # Dark grey clear
            renderer_instance.update(world) # This should draw entities, FPS text etc.
            
            # Explicitly draw a test rectangle to be SURE something is on screen
            if hasattr(renderer_instance.window, '_surface'): # Check if surface exists
                 import pygame # Local import for pygame.draw
                 pygame.draw.rect(renderer_instance.window._surface, (255,0,0), (10,10,50,50)) # Red square
                 pygame.draw.circle(renderer_instance.window._surface, (0,255,0), (100,100), 30) # Green circle


            renderer_instance.window.refresh()
        original_sleep() 

    tm.sleep_until_next_tick = gui_rendering_sleep_wrapper
    tm._gui_renderer_hook_instance = renderer_instance
    print("GUI rendering hook installed on TimeManager.")


def _uninstall_gui_hook(world: Any) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None: return
    if hasattr(tm, "_original_sleep_method_gui"):
        tm.sleep_until_next_tick = tm._original_sleep_method_gui
        delattr(tm, "_original_sleep_method_gui")
    if hasattr(tm, "_gui_renderer_hook_instance"):
        delattr(tm, "_gui_renderer_hook_instance")
    print("GUI rendering hook uninstalled from TimeManager.")


def gui(world: Any, state: Dict[str, Any]) -> None:
    current_gui_enabled_on_world = getattr(world, "gui_enabled", False)
    world.gui_enabled = not current_gui_enabled_on_world
    state["gui_enabled"] = world.gui_enabled
    renderer_instance = state.get("renderer") 
    if renderer_instance is None:
        print("Error: Renderer not found in state. GUI cannot be managed.")
        world.gui_enabled = False; state["gui_enabled"] = False; return
    if world.gui_enabled:
        _install_gui_hook(world, renderer_instance)
        print("GUI enabled. Window should appear/update.")
        if renderer_instance.window: # Initial render
            renderer_instance.window.clear((30,30,30)) # Clear with a visible color
            renderer_instance.update(world)
            if hasattr(renderer_instance.window, '_surface'): # Check if surface exists
                 import pygame
                 pygame.draw.rect(renderer_instance.window._surface, (0,0,255), (150,10,50,50)) # Blue square on toggle
            renderer_instance.window.refresh()
    else:
        _uninstall_gui_hook(world)
        print("GUI disabled.")


def help_command(state: Dict[str, Any]) -> None:
    print("\nAvailable commands:")
    print("  /help                - Show this help message.")
    print("  /gui                 - Toggle the Pygame GUI window.")
    print("  /pause               - Pause the simulation.")
    print("  /step                - Advance one tick if paused.")
    print("  /fps                 - Toggle live FPS display in console.")
    print("  /save [path]         - Save current world. Default: saves/world_state.json.gz")
    print("  /reload abilities    - Hot-reload abilities.")
    print("  /spawn <kind> [x] [y]- Spawn entity (npc, item). E.g., /spawn npc 5 5 or /spawn item")
    print("  /debug <entity_id>   - Print component data for an entity.")
    print("  /quit                - Exit the application.\n")


def execute(command: str, args: list[str], world: Any, state: Dict[str, Any]) -> None:
    if "running" not in state: state["running"] = True
    cmd_lower = command.lower() 
    if cmd_lower == "help": help_command(state)
    elif cmd_lower == "pause": pause(state)
    elif cmd_lower == "step": step(state)
    elif cmd_lower == "save": save(world, args[0] if args else None)
    elif cmd_lower == "reload" and args and args[0].lower() == "abilities": reload_abilities(world)
    elif cmd_lower == "profile": profile(world, args[0] if args else None)
    elif cmd_lower == "spawn" and args: spawn(world, args[0], args[1] if len(args) > 1 else None, args[2] if len(args) > 2 else None)
    elif cmd_lower == "debug" and args: debug(world, args[0])
    elif cmd_lower == "gui": gui(world, state)
    elif cmd_lower == "fps": fps(world, state)
    elif cmd_lower == "quit":
        state["running"] = False
        print("Quit command received. Shutting down...")
    else:
        print(f"Unknown command: /{command}. Type /help for available commands.")

__all__ = [
    "pause", "step", "save", "reload_abilities", "profile", "spawn", "debug",
    "gui", "fps", "help_command", "execute",
]