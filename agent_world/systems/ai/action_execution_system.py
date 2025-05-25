
# agent_world/systems/ai/action_execution_system.py
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
    GenerateAbilityAction,
    UseAbilityAction,
    PickupAction
)
from ..combat.combat_system import CombatSystem
from ...core.components.force import apply_force
from ...core.components.physics import Physics
from ...core.components.ai_state import AIState # Task 5.2
from ...systems.movement.movement_system import Velocity
# from ...ai.angel import generator as angel_generator # No longer directly used here
from ...ai.angel.system import get_angel_system
from ...systems.ability.ability_system import AbilitySystem
from ...core.components.known_abilities import KnownAbilitiesComponent

class ActionExecutionSystem:
    """Consume an :class:`ActionQueue` and enact results."""

    def __init__(self, world: Any, queue: ActionQueue, combat: CombatSystem) -> None:
        self.world = world
        self.queue = queue
        self.combat = combat

    def update(self, tick: int) -> None: 
        if self.world.component_manager is None:
            logging.error(f"[Tick {tick}] ActionExec: ComponentManager not found in world.")
            return
        cm = self.world.component_manager

        ability_system_instance: AbilitySystem | None = None
        if self.world.systems_manager:
            for system in self.world.systems_manager._systems: 
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
            logger.debug("[Tick %s] ActionExec: Processing %s for actor %s. Action: %s", tick, type(action).__name__, actor_id, action)

            if isinstance(action, MoveAction):
                if not cm.get_component(action.actor, Physics):
                    cm.add_component(action.actor, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
                apply_force(self.world, action.actor, float(action.dx), float(action.dy), ttl=1)
                if cm.get_component(action.actor, Velocity): # Remove direct velocity if force is applied
                    cm.remove_component(action.actor, Velocity)

            elif isinstance(action, AttackAction):
                self.combat.attack(action.actor, action.target, tick=tick)
            
            elif isinstance(action, LogAction):
                log_message = f"[Tick {tick}][Agent {action.actor} LOG]: {action.message}"
                logger.info(log_message)
            
            elif isinstance(action, IdleAction):
                pass 
            
            elif isinstance(action, GenerateAbilityAction):
                # Task 5.1 & 5.2
                angel_system = get_angel_system(self.world)
                queue_result = angel_system.queue_request(action.actor, action.description)
                
                ai_comp = cm.get_component(action.actor, AIState)
                if ai_comp:
                    ai_comp.waiting_for_ability_generation_desc = action.description
                
                # Only pause if request was successfully queued by AngelSystem
                if queue_result and queue_result.get("status") == "queued":
                    self.world.paused_for_angel = True 
                    logger.info(
                        "[Tick %s][ActionExec] Agent %s queued generation of ability '%s'. World PAUSED.",
                        tick, action.actor, action.description
                    )
                else:
                    logger.error(
                        "[Tick %s][ActionExec] Agent %s FAILED to queue generation for '%s'. Angel system issue: %s",
                        tick, action.actor, action.description, queue_result.get("reason", "unknown") if queue_result else "N/A"
                    )
                    if ai_comp: # Unset waiting flag if queueing failed
                        ai_comp.waiting_for_ability_generation_desc = None
                        ai_comp.last_error = f"Failed to queue ability generation: {queue_result.get('reason', 'unknown') if queue_result else 'N/A'}"
                        ai_comp.needs_immediate_rethink = True

            elif isinstance(action, UseAbilityAction):
                if ability_system_instance:
                    kab = cm.get_component(action.actor, KnownAbilitiesComponent)
                    if kab is None or action.ability_name not in kab.known_class_names:
                        logger.warning("[Tick %s][ActionExec] Agent %s attempted to use UNKNOWN ability '%s'.", tick, action.actor, action.ability_name)
                        ai_comp = cm.get_component(action.actor, AIState)
                        if ai_comp: 
                            ai_comp.last_error = f"Attempted to use unknown ability: {action.ability_name}"
                            ai_comp.last_action_failed_to_achieve_effect = True # Using unknown ability fails
                        continue

                    success = ability_system_instance.use(action.ability_name, action.actor, action.target_id)
                    ai_comp = cm.get_component(action.actor, AIState)
                    if success:
                        logger.info("[Tick %s][ActionExec] Agent %s successfully used ability '%s' (Target: %s).", tick, action.actor, action.ability_name, action.target_id)
                        if ai_comp: ai_comp.last_action_failed_to_achieve_effect = False
                    else:
                        logger.warning("[Tick %s][ActionExec] Agent %s FAILED to use ability '%s' (Target: %s). Check cooldown/can_use.", tick, action.actor, action.ability_name, action.target_id)
                        if ai_comp: 
                            ai_comp.last_error = f"Failed to use ability {action.ability_name}"
                            ai_comp.last_action_failed_to_achieve_effect = True
                else:
                    logger.error("[Tick %s][ActionExec] AbilitySystem not found. Cannot execute UseAbilityAction for agent %s.", tick, action.actor)
                    ai_comp = cm.get_component(action.actor, AIState)
                    if ai_comp: 
                        ai_comp.last_error = "AbilitySystem not available"
                        ai_comp.last_action_failed_to_achieve_effect = True


            elif isinstance(action, PickupAction):
                # Actual pickup logic is in PickupSystem. This action mainly serves as an intent.
                # For now, just log. PickupSystem will handle the mechanics.
                logger.info("[Tick %s][ActionExec] Agent %s intent to PICKUP item %s. (Actual pickup handled by PickupSystem)", tick, action.actor, action.item_id)

            else:
                logging.warning(f"[Tick {tick}] ActionExec: Unknown action type {type(action)} for actor {getattr(action, 'actor', 'N/A')}; treating as idle.")

__all__ = ["ActionExecutionSystem"]