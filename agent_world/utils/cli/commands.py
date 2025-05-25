
"""Implementations of development CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, TYPE_CHECKING
import logging

from ...core.components.position import Position
from ...core.components.health import Health
from ...core.components.inventory import Inventory
from ...core.components.ai_state import AIState # For spawning NPCs with AI
from ...core.components.physics import Physics # For spawning NPCs with Physics
from ...core.components.perception_cache import PerceptionCache # <<< ADDED
from ...systems.interaction.pickup import Tag
from ...core.components.role import RoleComponent
from ...core.components.known_abilities import KnownAbilitiesComponent
import yaml

logger = logging.getLogger(__name__)

from ...persistence.save_load import save_world
from ..observer import install_tick_observer, toggle_live_fps, print_fps as observer_print_fps

if TYPE_CHECKING:
    from ...gui.renderer import Renderer

try:
    from ..profiling import profile_ticks
except ImportError:
    def profile_ticks(n: int, tick_callback: Any, out_path: Any) -> None:
        logger.info("Profiling (stub): %s ticks, output to %s", n, out_path)
        pass


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")
ROLES_PATH = Path(__file__).resolve().parents[2] / "data" / "roles.yaml"
_ROLE_CACHE: Dict[str, Dict[str, Any]] | None = None


def _load_roles() -> Dict[str, Dict[str, Any]]:
    global _ROLE_CACHE
    if _ROLE_CACHE is not None:
        return _ROLE_CACHE
    if not ROLES_PATH.exists():
        _ROLE_CACHE = {}
        return _ROLE_CACHE
    try:
        data = yaml.safe_load(ROLES_PATH.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            data = {}
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Error loading roles file: %s", e)
        data = {}
    _ROLE_CACHE = {str(k): v for k, v in data.items() if isinstance(v, dict)}
    return _ROLE_CACHE


def pause(state: Dict[str, Any]) -> None:
    state["paused"] = True
    logger.info("Simulation paused.")


def step(state: Dict[str, Any]) -> None:
    if state.get("paused", False):
        state["step"] = True
        logger.info("Stepping one tick.")
    else:
        logger.info("Simulation is not paused. Use /pause first.")


def save(world: Any, path: str | Path | None = None) -> None:
    save_path = Path(path) if path is not None else DEFAULT_SAVE_PATH
    try:
        save_world(world, save_path)
        logger.info("World saved to %s", save_path)
    except Exception as e:
        logger.error("Error saving world: %s", e)


def reload_abilities(world: Any) -> None:
    sm: Iterable[Any] | None = getattr(world, "systems_manager", None)
    if sm is None:
        logger.error("SystemsManager not found in world.")
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
                    logger.error(
                        "Error reloading abilities in system %s: %s",
                        type(system).__name__,
                        e,
                    )
    if reloaded_count > 0:
        logger.info("Abilities reloaded for %s system(s).", reloaded_count)
    else:
        logger.info("No ability systems found or reloaded.")


def profile(world: Any, ticks_str: str | None = None) -> None:
    try:
        num_ticks = int(ticks_str) if ticks_str else 100
        if num_ticks <= 0:
            logger.info("Number of ticks must be positive.")
            return
    except ValueError:
        logger.error("Invalid number of ticks: %s", ticks_str)
        return
    out_path = Path("profile.prof")
    logger.info("Starting profiling for %s ticks. Output to %s", num_ticks, out_path)
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
        logger.error("World components missing for profiling callback setup.")
        return
    try:
        profile_ticks(num_ticks, single_world_tick_for_profiling, out_path)
        logger.info("Profiling complete. Stats saved to %s", out_path)
    except Exception as e:
        logger.error("Error during profiling: %s", e)


def spawn(world: Any, kind: str, x_str: str | None = None, y_str: str | None = None) -> int | None:
    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    spatial_index = getattr(world, "spatial_index", None)
    if em is None or cm is None or spatial_index is None:
        logger.error("World managers not initialized for spawn.")
        return None

    role_name: str | None = None
    if ":" in kind:
        kind, role_name = kind.split(":", 1)
    kind_lower = kind.lower()
    if kind_lower == "npc" and x_str and not x_str.lstrip("-").isdigit():
        role_name = x_str
        x_str = None
        y_str = None

    default_x = world.size[0] // 2 if hasattr(world, 'size') else 0
    default_y = world.size[1] // 2 if hasattr(world, 'size') else 0
    try:
        x = int(x_str) if x_str and x_str.lstrip('-').isdigit() else default_x
        y = int(y_str) if y_str and y_str.lstrip('-').isdigit() else default_y
    except ValueError:
        logger.error(
            "Invalid coordinates for spawn ('%s', '%s'). Using defaults (%s,%s).",
            x_str,
            y_str,
            default_x,
            default_y,
        )
        x = default_x
        y = default_y

    ent_id = em.create_entity()
    cm.add_component(ent_id, Position(x, y))
    kind_lower = kind.lower()

    if kind_lower == "npc":
        cm.add_component(ent_id, Health(cur=10, max=10))
        cm.add_component(ent_id, Inventory(capacity=4))
        cm.add_component(ent_id, AIState(personality="curious_explorer_" + str(ent_id), goals=[]))
        cm.add_component(ent_id, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
        cm.add_component(ent_id, PerceptionCache(visible=[], last_tick=-1))
        if role_name:
            role_data = _load_roles().get(role_name)
            if role_data:
                role_comp = RoleComponent(
                    role_name=role_name,
                    can_request_abilities=bool(role_data.get("can_request_abilities", True)),
                    uses_llm=bool(role_data.get("uses_llm", True)),
                    fixed_abilities=list(role_data.get("fixed_abilities", [])),
                )
                cm.add_component(ent_id, role_comp)
                if role_comp.fixed_abilities:
                    cm.add_component(ent_id, KnownAbilitiesComponent(role_comp.fixed_abilities.copy()))
            else:
                logger.warning("Unknown role '%s'. NPC spawned without role data.", role_name)
        logger.info(
            "Spawned NPC (ID: %s) at (%s,%s) with AIState, Physics, and PerceptionCache",
            ent_id,
            x,
            y,
        )
    elif kind_lower == "item":
        cm.add_component(ent_id, Tag("item"))
        logger.info("Spawned Item (ID: %s) at (%s,%s)", ent_id, x, y)
    else:
        em.destroy_entity(ent_id)
        logger.error("Unknown entity kind for spawn: '%s'. Known: npc, item.", kind)
        return None

    spatial_index.insert(ent_id, (x, y))

    return ent_id


def debug(world: Any, entity_id_str: str | None) -> None:
    if entity_id_str is None:
        logger.info("Usage: /debug <entity_id>")
        return
    try:
        entity_id = int(entity_id_str)
    except ValueError:
        logger.error("Invalid entity id: %s", entity_id_str)
        return
    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    if em is None or cm is None:
        logger.error("World managers not initialized for debug.")
        return
    if not em.has_entity(entity_id):
        logger.error("Entity %s not found.", entity_id)
        return
    entity_component_map = cm._components.get(entity_id)
    logger.info("--- Entity %s Components ---", entity_id)
    if entity_component_map:
        for name_type, comp_instance in entity_component_map.items(): # Iterate over type and instance
             comp_name_str = name_type.__name__ if isinstance(name_type, type) else str(name_type)
             logger.info("  %s: %s", comp_name_str, comp_instance)
    else:
        logger.info("  No components found for this entity.")
    logger.info("-----------------------------")


def fps(world: Any, state: Dict[str, Any]) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is not None: 
        install_tick_observer(tm)
        fps_is_now_enabled = toggle_live_fps()
        state["fps_enabled"] = fps_is_now_enabled
        world.fps_enabled = fps_is_now_enabled
        if fps_is_now_enabled:
            logger.info("Live FPS display enabled.")
            observer_print_fps()
        else:
            logger.info("Live FPS display disabled.")


def _install_follow_hook(world: Any, renderer_instance: Renderer, state: Dict[str, Any]) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None or renderer_instance is None:
        logger.error("TimeManager or renderer not found. Cannot follow entity.")
        return
    if getattr(tm, "_follow_hook_installed", False):
        return
    original_sleep = tm.sleep_until_next_tick

    def follow_sleep_wrapper() -> None:
        ent_id = state.get("follow_entity_id")
        if ent_id is not None:
            renderer_instance.center_on_entity(ent_id)
        original_sleep()

    tm.sleep_until_next_tick = follow_sleep_wrapper
    tm._follow_hook_installed = True


def _install_gui_hook(world: Any, renderer_instance: Renderer) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None:
        logger.error("TimeManager not found. Cannot install GUI hook.")
        return
    if getattr(tm, "_gui_renderer_hook_instance", None) == renderer_instance: return
    if not hasattr(tm, "_original_sleep_method_gui"):
        tm._original_sleep_method_gui = tm.sleep_until_next_tick
    original_sleep = tm._original_sleep_method_gui

    def gui_rendering_sleep_wrapper() -> None:
        if getattr(world, "gui_enabled", False) and renderer_instance and renderer_instance.window:
            if hasattr(renderer_instance.window, '_surface'): # Check if surface exists
                 renderer_instance.window.clear((30, 30, 30))
                 renderer_instance.update(world)
                 renderer_instance.window.refresh()
        original_sleep()

    tm.sleep_until_next_tick = gui_rendering_sleep_wrapper
    tm._gui_renderer_hook_instance = renderer_instance
    # print("GUI rendering hook installed on TimeManager.") # Can be verbose


def _uninstall_gui_hook(world: Any) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None: return
    if hasattr(tm, "_original_sleep_method_gui"):
        tm.sleep_until_next_tick = tm._original_sleep_method_gui
        delattr(tm, "_original_sleep_method_gui")
    if hasattr(tm, "_gui_renderer_hook_instance"):
        delattr(tm, "_gui_renderer_hook_instance")
    # print("GUI rendering hook uninstalled from TimeManager.") # Can be verbose


def gui(world: Any, state: Dict[str, Any]) -> None:
    current_gui_enabled_on_world = getattr(world, "gui_enabled", False)
    world.gui_enabled = not current_gui_enabled_on_world
    state["gui_enabled"] = world.gui_enabled
    renderer_instance = state.get("renderer")
    if renderer_instance is None:
        logger.error("Error: Renderer not found in state. GUI cannot be managed.")
        world.gui_enabled = False; state["gui_enabled"] = False; return
    if world.gui_enabled:
        _install_gui_hook(world, renderer_instance)
        logger.info("GUI enabled. Window should appear/update.")
        if renderer_instance.window and hasattr(renderer_instance.window, '_surface'):
            renderer_instance.window.clear((30,30,30))
            renderer_instance.update(world)
            renderer_instance.window.refresh()
    else:
        _uninstall_gui_hook(world)
        logger.info("GUI disabled.")


def follow(world: Any, entity_id_str: str | None, state: Dict[str, Any]) -> None:
    renderer_instance = state.get("renderer")
    if renderer_instance is None:
        logger.error("Error: Renderer not found in state. Cannot follow entity.")
        return
    if entity_id_str is None:
        logger.info("Usage: /follow <entity_id>")
        return
    try:
        entity_id = int(entity_id_str)
    except ValueError:
        logger.error("Invalid entity id: %s", entity_id_str)
        return
    state["follow_entity_id"] = entity_id
    _install_follow_hook(world, renderer_instance, state)
    logger.info("Following entity %s", entity_id)


def scenario(world: Any, name: str) -> None:
    """Load and run a scenario by name."""

    name = name.lower()
    if name == "default_pickup":
        from ...scenarios.default_pickup_scenario import DefaultPickupScenario

        DefaultPickupScenario().setup(world)
    else:
        logger.error("Unknown scenario: %s", name)


def help_command(state: Dict[str, Any]) -> None:
    help_lines = [
        "\nAvailable commands:",
        "  /help                - Show this help message.",
        "  /gui                 - Toggle the Pygame GUI window.",
        "  /pause               - Pause the simulation.",
        "  /step                - Advance one tick if paused.",
        "  /fps                 - Toggle live FPS display in console.",
        "  /save [path]         - Save current world. Default: saves/world_state.json.gz",
        "  /reload abilities    - Hot-reload abilities.",
        "  /spawn <kind> [x] [y]- Spawn entity (npc, item). E.g., /spawn npc 5 5 or /spawn item",
        "  /debug <entity_id>   - Print component data for an entity.",
        "  /follow <entity_id>  - Center camera on an entity each tick.",
        "  /scenario <name>     - Load a scenario by name (e.g., default_pickup).",
        "  /quit                - Exit the application.\n",
    ]
    for line in help_lines:
        logger.info(line)


def execute(command: str, args: list[str], world: Any, state: Dict[str, Any]) -> Any:
    # +++ UNMISSABLE DEBUG PRINT +++
    logger.debug("TOP OF commands.execute CALLED! command: %s", command)
    # +++ END UNMISSABLE DEBUG PRINT +++

    if "running" not in state: state["running"] = True
    cmd_lower = command.lower()
    
    return_value: Any = None 

    if cmd_lower == "spawn" and args:
        spawned_id = spawn(world, args[0], args[1] if len(args) > 1 else None, args[2] if len(args) > 2 else None)
        logger.debug(
            "DEBUG commands.execute: spawn() returned: %s, type: %s",
            spawned_id,
            type(spawned_id),
        )
        return_value = spawned_id 
    elif cmd_lower == "help":
        help_command(state)
        # return_value remains None
    elif cmd_lower == "pause":
        pause(state)
        # return_value remains None
    elif cmd_lower == "step":
        step(state)
        # return_value remains None
    elif cmd_lower == "save":
        save(world, args[0] if args else None)
        # return_value remains None
    elif cmd_lower == "reload" and args and args[0].lower() == "abilities":
        reload_abilities(world)
        # return_value remains None
    elif cmd_lower == "profile":
        profile(world, args[0] if args else None)
        # return_value remains None
    elif cmd_lower == "debug" and args:
        debug(world, args[0])
        # return_value remains None
    elif cmd_lower == "gui":
        gui(world, state)
        # return_value remains None
    elif cmd_lower == "fps":
        fps(world, state)
        # return_value remains None
    elif cmd_lower == "follow" and args:
        follow(world, args[0], state)
        # return_value remains None
    elif cmd_lower == "scenario" and args:
        scenario(world, args[0])
        # return_value remains None
    elif cmd_lower == "quit":
        state["running"] = False
        logger.info("Quit command received. Shutting down...")
        # return_value remains None
    else:
        logger.error("Unknown command: /%s. Type /help for available commands.", command)
        # return_value remains None
    
    return return_value # Explicitly return the captured value (or None if not set)

__all__ = [
    "pause", "step", "save", "reload_abilities", "profile", "spawn", "debug",
    "gui", "fps", "follow", "scenario", "help_command", "execute",
]