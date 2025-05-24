"""Translate queued actions into world effects."""

from __future__ import annotations

from typing import Any

import logging

from .actions import (
    ActionQueue,
    MoveAction,
    AttackAction,
    LogAction,
    IdleAction,
)
from ..combat.combat_system import CombatSystem
from ..movement.movement_system import Velocity
from ...core.components.force import apply_force


class ActionExecutionSystem:
    """Consume an :class:`ActionQueue` and enact results."""

    def __init__(self, world: Any, queue: ActionQueue, combat: CombatSystem) -> None:
        self.world = world
        self.queue = queue
        self.combat = combat

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def update(self, tick: int) -> None:
        """Apply queued actions for this tick."""

        if self.world.component_manager is None:
            return

        cm = self.world.component_manager
        while True:
            action = self.queue.pop()
            if action is None:
                break

            if isinstance(action, MoveAction):
                apply_force(self.world, action.actor, action.dx, action.dy, ttl=1)
                cm.remove_component(action.actor, Velocity)
            elif isinstance(action, AttackAction):
                self.combat.attack(action.actor, action.target, tick=tick)
            elif isinstance(action, LogAction):
                print(action.message)
            elif isinstance(action, IdleAction):
                pass
            else:
                logging.warning("Unknown action %r; treating as idle", action)


__all__ = ["ActionExecutionSystem"]
