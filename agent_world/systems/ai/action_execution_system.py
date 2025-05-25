
"""Translate queued actions into world effects."""

from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)

from .actions import (
    ActionQueue,
    MoveAction,
    AttackAction,
    LogAction,
    IdleAction,
    GenerateAbilityAction, # <<< IMPORTED
    UseAbilityAction,      # <<< IMPORTED
    PickupAction           # <<< IMPORTED (for future Phase 23)
)
from ..combat.combat_system import CombatSystem
from ...core.components.force import apply_force
from ...core.components.physics import Physics
from ...systems.movement.movement_system import Velocity
from ...ai.angel import generator as angel_generator
from ...ai.angel.system import get_angel_system
from ...systems.ability.ability_system import AbilitySystem # <<< For finding AbilitySystem
from ...core.components.known_abilities import KnownAbilitiesComponent

class ActionExecutionSystem:
    """Consume an :class:`ActionQueue` and enact results."""

    def __init__(self, world: Any, queue: ActionQueue, combat: CombatSystem) -> None:
        self.world = world
        self.queue = queue
        self.combat = combat

    def update(self, tick: int) -> None: 
        """Apply queued actions for this tick."""

        if self.world.component_manager is None:
            logging.error(f"[Tick {tick}] ActionExec: ComponentManager not found in world.")
            return
        cm = self.world.component_manager

        # Try to get AbilitySystem instance once per update if needed
        ability_system_instance: AbilitySystem | None = None
        if self.world.systems_manager:
            for system in self.world.systems_manager._systems: # Accessing internal list for type check
                if isinstance(system, AbilitySystem):
                    ability_system_instance = system
                    break
        
        if hasattr(self.world, 'ability_system_instance') and self.world.ability_system_instance is not None:
            ability_system_instance = self.world.ability_system_instance


        while True:
            action = self.queue.pop()
            if action is None:
                break
            
            actor_id = getattr(action, 'actor', 'N/A')
            logger.debug(
                "[Tick %s] ActionExec: Processing %s for actor %s. Action: %s",
                tick,
                type(action).__name__,
                actor_id,
                action,
            )

            if isinstance(action, MoveAction):
                if not cm.get_component(action.actor, Physics):
                    logger.debug(
                        "[Tick %s] ActionExec: Actor %s missing Physics component for MoveAction. Adding one.",
                        tick,
                        action.actor,
                    )
                    cm.add_component(action.actor, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
                
                logger.debug(
                    "[Tick %s] ActionExec: Applying force for MoveAction: dx=%s, dy=%s to entity %s",
                    tick,
                    action.dx,
                    action.dy,
                    action.actor,
                )
                apply_force(self.world, action.actor, float(action.dx), float(action.dy), ttl=1)
                if cm.get_component(action.actor, Velocity):
                    cm.remove_component(action.actor, Velocity)

            elif isinstance(action, AttackAction):
                logger.debug(
                    "[Tick %s] ActionExec: Actor %s performing AttackAction on target %s",
                    tick,
                    action.actor,
                    action.target,
                )
                self.combat.attack(action.actor, action.target, tick=tick)
            
            elif isinstance(action, LogAction):
                log_message = f"[Tick {tick}][Agent {action.actor} LOG]: {action.message}"
                logger.info(log_message)
            
            elif isinstance(action, IdleAction):
                pass 
            
            # --- HANDLE GenerateAbilityAction ---
            elif isinstance(action, GenerateAbilityAction):
                self.world.paused_for_angel = True
                angel_system = get_angel_system(self.world)
                try:
                    angel_system.queue_request(action.actor, action.description)
                    logger.info(
                        "[Tick %s][ActionExec] Agent %s queued generation of ability '%s'.",
                        tick,
                        action.actor,
                        action.description,
                    )
                except Exception as e:
                    error_msg = (
                        f"Error during ability generation request for agent {action.actor} "
                        f"(desc: '{action.description}'): {e}"
                    )
                    logger.error("[Tick %s][ActionExec] %s", tick, error_msg)
                finally:
                    self.world.paused_for_angel = False
            
            # --- HANDLE UseAbilityAction ---
            elif isinstance(action, UseAbilityAction):
                if ability_system_instance:
                    kab = cm.get_component(action.actor, KnownAbilitiesComponent)
                    if kab is None or action.ability_name not in kab.known_class_names:
                        logger.info(
                            "[Tick %s][ActionExec] Agent %s does not possess ability '%s'.",
                            tick,
                            action.actor,
                            action.ability_name,
                        )
                        continue

                    success = ability_system_instance.use(
                        action.ability_name, action.actor, action.target_id
                    )
                    if success:
                        logger.info(
                            "[Tick %s][ActionExec] Agent %s successfully used ability '%s' (Target: %s).",
                            tick,
                            action.actor,
                            action.ability_name,
                            action.target_id,
                        )
                    else:
                        logger.warning(
                            "[Tick %s][ActionExec] Agent %s FAILED to use ability '%s' (Target: %s). Check cooldown/can_use.",
                            tick,
                            action.actor,
                            action.ability_name,
                            action.target_id,
                        )
                else:
                    logger.error(
                        "[Tick %s][ActionExec] AbilitySystem not found. Cannot execute UseAbilityAction for agent %s.",
                        tick,
                        action.actor,
                    )

            # --- HANDLE PickupAction (Placeholder for now, actual logic in Phase 23) ---
            elif isinstance(action, PickupAction):
                # For Phase 22, we are just logging it was requested.
                # Actual pickup logic will be in Phase 23.
                logger.info(
                    "[Tick %s][ActionExec] Agent %s requested PICKUP for item %s. (Execution logic pending Phase 23)",
                    tick,
                    action.actor,
                    action.item_id,
                )
                # Placeholder: In Phase 23, this would call something like:
                # pickup_system = self.world.systems_manager.get_system(PickupSystem) # or self.world.pickup_system_instance
                # if pickup_system:
                #     pickup_system.pickup_item(action.actor, action.item_id)
                # else:
                #     print(f"[Tick {tick}][ActionExec ERROR] PickupSystem not found for PICKUP action.")


            else:
                logging.warning(f"[Tick {tick}] ActionExec: Unknown action type {type(action)} for actor {getattr(action, 'actor', 'N/A')}; treating as idle.")

__all__ = ["ActionExecutionSystem"]