"""Implementations of development CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from ...core.components.position import Position
from ...core.components.health import Health
from ...core.components.inventory import Inventory
from ...systems.interaction.pickup import Tag

from ...persistence.save_load import save_world
from ..observer import install_tick_observer, toggle_live_fps
from ...gui.renderer import Renderer

# GUI rendering globals
_renderer = Renderer()
_gui_enabled: bool = False

try:  # utils.profiling may not implement profile_ticks yet
    from ..profiling import profile_ticks
except Exception:  # pragma: no cover - fallback for placeholder module

    def profile_ticks(world: Any, ticks: int) -> None:
        pass


DEFAULT_SAVE_PATH = Path("saves/world_state.json.gz")


def pause(state: Dict[str, Any]) -> None:
    """Set ``state['paused']`` to ``True``."""

    state["paused"] = True


def step(state: Dict[str, Any]) -> None:
    """Request a single tick while paused."""

    state["step"] = True


def save(world: Any, path: str | Path | None = None) -> None:
    """Serialize ``world`` to ``path`` or ``DEFAULT_SAVE_PATH``."""

    save_world(world, Path(path) if path is not None else DEFAULT_SAVE_PATH)


def reload_abilities(world: Any) -> None:
    """Force ability hot-reload by calling ``update`` on the ability system."""

    sm: Iterable[Any] | None = getattr(world, "systems_manager", None)
    if sm is None:
        return
    for system in sm:
        if hasattr(system, "abilities"):
            update = getattr(system, "update", None)
            if callable(update):
                update()


def profile(world: Any, ticks: int) -> None:
    """Run :func:`profile_ticks` for ``ticks``."""

    profile_ticks(world, ticks)


def spawn(world: Any, kind: str) -> int | None:
    """Spawn an entity of ``kind`` and return its ID."""

    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    if em is None or cm is None:
        return None

    ent = em.create_entity()
    if kind == "npc":
        cm.add_component(ent, Position(0, 0))
        cm.add_component(ent, Health(cur=10, max=10))
        cm.add_component(ent, Inventory(capacity=4))
    elif kind == "item":
        cm.add_component(ent, Position(0, 0))
        cm.add_component(ent, Tag("item"))
    elif kind == "ability":
        cm.add_component(ent, Position(0, 0))
        cm.add_component(ent, Tag("ability"))
    else:
        em.destroy_entity(ent)
        return None
    return ent


def debug(world: Any, entity_id: int) -> None:
    """Print a dump of components for ``entity_id``."""

    em = getattr(world, "entity_manager", None)
    cm = getattr(world, "component_manager", None)
    if em is None or cm is None or not em.has_entity(entity_id):
        print(f"Entity {entity_id} not found")
        return

    comps = cm._components.get(entity_id, {})
    print(f"Entity {entity_id} components:")
    for name, comp in comps.items():
        print(f"  {name}: {comp}")

def fps(world: Any, state: Dict[str, Any]) -> None:
    """Toggle live FPS printing for the tick loop."""

    tm = getattr(world, "time_manager", None)
    if tm is not None:
        install_tick_observer(tm)
    state["fps"] = toggle_live_fps()


def _install_gui_hook(world: Any) -> None:
    tm = getattr(world, "time_manager", None)
    if tm is None or hasattr(tm, "_gui_wrapped"):
        return

    original = tm.sleep_until_next_tick

    def wrapper() -> None:
        if _gui_enabled:
            _renderer.update(world)
            _renderer.window.refresh()
        original()

    tm.sleep_until_next_tick = wrapper  # type: ignore[assignment]
    setattr(tm, "_gui_wrapped", True)


def gui(world: Any, state: Dict[str, Any]) -> None:
    """Toggle GUI rendering on or off."""

    global _gui_enabled
    _gui_enabled = not _gui_enabled
    state["gui_enabled"] = _gui_enabled
    _install_gui_hook(world)
    if _gui_enabled:
        _renderer.update(world)
        _renderer.window.refresh()



def execute(command: str, args: list[str], world: Any, state: Dict[str, Any]) -> None:
    """Dispatch ``command`` with ``args``."""

    if command == "pause":
        pause(state)
    elif command == "step":
        step(state)
    elif command == "save":
        save(world, args[0] if args else None)
    elif command == "reload" and args and args[0] == "abilities":
        reload_abilities(world)
    elif command == "profile":
        profile(world, int(args[0]) if args else 1)
    elif command == "spawn" and args:
        spawn(world, args[0])
    elif command == "debug" and args:
        try:
            ent = int(args[0])
        except ValueError:
            print(f"Invalid entity id: {args[0]}")
        else:
            debug(world, ent)
    elif command == "gui":
        gui(world, state)
    elif command == "fps":
        fps(world, state)


__all__ = [
    "pause",
    "step",
    "save",
    "reload_abilities",
    "profile",
    "spawn",
    "debug",
    "gui",
    "fps",
    "execute",
]
