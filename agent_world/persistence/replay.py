"""Utility for deterministic event replay."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

from ..systems.combat.combat_system import CombatSystem
from ..systems.combat.damage_types import DamageType

# Event type alias for readability
Event = Dict[str, Any]
# Callback signature used for applying an event to the world
EventHandler = Callable[[Any, Event, List[Event]], None]


def _default_handlers() -> Dict[str, EventHandler]:
    """Return built-in handlers for core event types."""

    def _handle_attack(world: Any, event: Event, log: List[Event]) -> None:
        """Replay a combat attack event."""

        cs = CombatSystem(world, log)
        damage_type = DamageType[event.get("damage_type", "MELEE")]
        cs.attack(
            attacker=event["attacker"],
            target=event["target"],
            damage_type=damage_type,
            tick=event.get("tick"),
        )

    return {"attack": _handle_attack}


def replay(
    world_factory: Callable[[], Any],
    events: Iterable[Event],
    handlers: Dict[str, EventHandler] | None = None,
) -> tuple[Any, bool]:
    """Re-run events against a fresh world and verify determinism.

    Parameters
    ----------
    world_factory:
        Callable returning a new world instance configured for the test.
    events:
        Iterable of events previously produced by the world.
    handlers:
        Optional mapping of ``event_type`` strings to replay callbacks.

    Returns
    -------
    tuple[Any, bool]
        The new world after replay and ``True`` if the produced event log
        matches ``events`` exactly.
    """

    events_list = list(events)
    world = world_factory()
    tm = getattr(world, "time_manager", None)
    handlers = handlers or _default_handlers()

    out_log: List[Event] = []
    for event in events_list:
        tick = event.get("tick")
        if tm is not None and tick is not None:
            tm.tick_counter = tick
        handler = handlers.get(event.get("type"))
        if handler is not None:
            handler(world, event, out_log)

    return world, out_log == events_list


__all__ = ["replay", "Event", "EventHandler"]
