
"""Translate queued actions into world effects."""

from __future__ import annotations

from typing import Any
import logging # For warning on unknown actions

from .actions import (
    ActionQueue,
    MoveAction,
    AttackAction,
    LogAction, # Assuming LogAction is defined
    IdleAction # Assuming IdleAction is defined
)
from ..combat.combat_system import CombatSystem
from ...core.components.force import apply_force
from ...core.components.physics import Physics # For type hinting if needed
from ...systems.movement.movement_system import Velocity # For removing old velocity comp


class ActionExecutionSystem:
    """Consume an :class:`ActionQueue` and enact results."""

    def __init__(self, world: Any, queue: ActionQueue, combat: CombatSystem) -> None:
        self.world = world
        self.queue = queue
        self.combat = combat

    def update(self, tick: int) -> None: # tick is passed from SystemsManager
        """Apply queued actions for this tick."""

        if self.world.component_manager is None:
            return
        cm = self.world.component_manager

        while True:
            action = self.queue.pop()
            if action is None:
                break
            
            # --- LOGGING: Action Execution ---
            print(f"[Tick {tick}] ActionExec: Processing {action} for actor {getattr(action, 'actor', 'N/A')}")
            # --- END LOGGING ---

            if isinstance(action, MoveAction):
                # Ensure entity has a Physics component for force application
                if not cm.get_component(action.actor, Physics):
                    print(f"[Tick {tick}] ActionExec: Actor {action.actor} missing Physics component for MoveAction. Adding one.")
                    cm.add_component(action.actor, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
                
                print(f"[Tick {tick}] ActionExec: Applying force for MoveAction: dx={action.dx}, dy={action.dy} to entity {action.actor}")
                apply_force(self.world, action.actor, float(action.dx), float(action.dy), ttl=1)
                # Remove old Velocity component if it exists from a previous movement system version
                if cm.get_component(action.actor, Velocity):
                    cm.remove_component(action.actor, Velocity)

            elif isinstance(action, AttackAction):
                print(f"[Tick {tick}] ActionExec: Actor {action.actor} performing AttackAction on target {action.target}")
                self.combat.attack(action.actor, action.target, tick=tick)
            
            elif isinstance(action, LogAction):
                log_message = f"[Tick {tick}][Agent {action.actor} LOG]: {action.message}"
                print(log_message)
            
            elif isinstance(action, IdleAction):
                # print(f"[Tick {tick}] ActionExec: Actor {action.actor} is IDLE.") # Can be verbose
                pass # No operation for idle

            else:
                logging.warning(f"[Tick {tick}] ActionExec: Unknown action type {type(action)} for actor {getattr(action, 'actor', 'N/A')}; treating as idle.")
                # Optionally, create and process an IdleAction here
                # idle_action = IdleAction(actor=getattr(action, 'actor', -1)) # Get actor if possible
                # print(f"[Tick {tick}] ActionExec: Processing {idle_action} for actor {idle_action.actor}")


__all__ = ["ActionExecutionSystem"]