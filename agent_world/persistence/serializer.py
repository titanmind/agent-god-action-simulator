"""Helpers for serializing the world state to JSON."""

from __future__ import annotations

import importlib
from dataclasses import asdict, is_dataclass
from typing import Any, Dict

# Import components so their classes are discoverable during deserialisation.
from ..core.components.known_abilities import KnownAbilitiesComponent  # noqa: F401
from ..core.components.role import RoleComponent                       # noqa: F401


def _class_path(obj: Any) -> str:
    """Return the fully-qualified class path for ``obj``."""

    cls = obj.__class__
    return f"{cls.__module__}.{cls.__name__}"


def serialize(obj: Any) -> Any:
    """Recursively convert ``obj`` into JSON-serialisable data."""

    if is_dataclass(obj):
        data = {k: serialize(v) for k, v in asdict(obj).items()}
        data["__class__"] = _class_path(obj)
        return data
    if isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize(v) for v in obj]
    return obj


def deserialize(data: Any) -> Any:
    """Reconstruct Python objects from ``data`` produced by :func:`serialize`."""

    if isinstance(data, dict):
        if "__class__" in data:
            class_path = data.pop("__class__")
            module_name, cls_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            cls = getattr(module, cls_name)
            kwargs = {k: deserialize(v) for k, v in data.items()}
            return cls(**kwargs)
        return {k: deserialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [deserialize(v) for v in data]
    return data


def world_to_dict(world: "World") -> Dict[str, Any]:
    """Serialize ``world`` into a dictionary."""

    entities: Dict[str, Dict[str, Any]] = {}
    if world.entity_manager is not None:
        for eid, comps in world.entity_manager.all_entities.items():
            entities[str(eid)] = {name: serialize(comp) for name, comp in comps.items()}

    tick = world.time_manager.tick_counter if world.time_manager else 0

    return {
        "size": list(world.size),
        "tile_map": serialize(world.tile_map),
        "entities": entities,
        "tick_counter": tick,
    }


def world_from_dict(data: Dict[str, Any]) -> "World":
    """Create a ``World`` instance from ``data`` produced by :func:`world_to_dict`."""

    from agent_world.core.world import World
    from agent_world.core.entity_manager import EntityManager
    from agent_world.core.component_manager import ComponentManager
    from agent_world.core.time_manager import TimeManager

    world = World(tuple(data.get("size", (10, 10))))

    world.tile_map = deserialize(data.get("tile_map", []))

    em = EntityManager()
    entities_data = data.get("entities", {})
    max_id = 0
    for eid_str, comps in entities_data.items():
        eid = int(eid_str)
        max_id = max(max_id, eid)
        em._entity_components[eid] = {
            name: deserialize(val) for name, val in comps.items()
        }
    em._next_id = max_id
    world.entity_manager = em

    cm = ComponentManager()
    for eid, comps in em._entity_components.items():
        for comp in comps.values():
            cm.add_component(eid, comp)
    world.component_manager = cm

    tm = TimeManager()
    tm.tick_counter = int(data.get("tick_counter", 0))
    world.time_manager = tm

    return world


__all__ = [
    "serialize",
    "deserialize",
    "world_to_dict",
    "world_from_dict",
]
