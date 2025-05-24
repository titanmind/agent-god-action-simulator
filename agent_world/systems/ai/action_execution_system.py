
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
    GenerateAbilityAction, # <<< IMPORTED
    UseAbilityAction,      # <<< IMPORTED
    PickupAction           # <<< IMPORTED (for future Phase 23)
)
from ..combat.combat_system import CombatSystem
from ...core.components.force import apply_force
from ...core.components.physics import Physics 
from ...systems.movement.movement_system import Velocity 
from ...ai.angel import generator as angel_generator # <<< IMPORTED angel_generator
from ...systems.ability.ability_system import AbilitySystem # <<< For finding AbilitySystem

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
            print(f"[Tick {tick}] ActionExec: Processing {type(action).__name__} for actor {actor_id}. Action: {action}")

            if isinstance(action, MoveAction):
                if not cm.get_component(action.actor, Physics):
                    print(f"[Tick {tick}] ActionExec: Actor {action.actor} missing Physics component for MoveAction. Adding one.")
                    cm.add_component(action.actor, Physics(mass=1.0, vx=0.0, vy=0.0, friction=0.95))
                
                # print(f"[Tick {tick}] ActionExec: Applying force for MoveAction: dx={action.dx}, dy={action.dy} to entity {action.actor}") # Verbose
                apply_force(self.world, action.actor, float(action.dx), float(action.dy), ttl=1)
                if cm.get_component(action.actor, Velocity):
                    cm.remove_component(action.actor, Velocity)

            elif isinstance(action, AttackAction):
                # print(f"[Tick {tick}] ActionExec: Actor {action.actor} performing AttackAction on target {action.target}") # Verbose
                self.combat.attack(action.actor, action.target, tick=tick)
            
            elif isinstance(action, LogAction):
                log_message = f"[Tick {tick}][Agent {action.actor} LOG]: {action.message}"
                print(log_message)
            
            elif isinstance(action, IdleAction):
                pass 
            
            # --- HANDLE GenerateAbilityAction ---
            elif isinstance(action, GenerateAbilityAction):
                self.world.paused_for_angel = True
                try:
                    generated_path = angel_generator.generate_ability(action.description)
                    log_msg = (
                        f"Agent {action.actor} requested generation of ability: '{action.description}'. "
                        f"File created: {generated_path}"
                    )
                    print(f"[Tick {tick}][ActionExec] {log_msg}")
                    # Optional: Log this as a game event too via world.event_log or similar
                    # self.world.event_log.append({"type": "ability_generated", "tick": tick, "actor": action.actor, "description": action.description, "path": str(generated_path)})
                except Exception as e:
                    error_msg = (
                        f"Error during ability generation for agent {action.actor} "
                        f"(desc: '{action.description}'): {e}"
                    )
                    print(f"[Tick {tick}][ActionExec ERROR] {error_msg}")
                finally:
                    self.world.paused_for_angel = False
            
            # --- HANDLE UseAbilityAction ---
            elif isinstance(action, UseAbilityAction):
                if ability_system_instance:
                    success = ability_system_instance.use(action.ability_name, action.actor, action.target_id)
                    if success:
                        print(f"[Tick {tick}][ActionExec] Agent {action.actor} successfully used ability '{action.ability_name}' (Target: {action.target_id}).")
                    else:
                        print(f"[Tick {tick}][ActionExec] Agent {action.actor} FAILED to use ability '{action.ability_name}' (Target: {action.target_id}). Check cooldown/can_use.")
                else:
                    print(f"[Tick {tick}][ActionExec ERROR] AbilitySystem not found. Cannot execute UseAbilityAction for agent {action.actor}.")

            # --- HANDLE PickupAction (Placeholder for now, actual logic in Phase 23) ---
            elif isinstance(action, PickupAction):
                # For Phase 22, we are just logging it was requested.
                # Actual pickup logic will be in Phase 23.
                print(f"[Tick {tick}][ActionExec] Agent {action.actor} requested PICKUP for item {action.item_id}. (Execution logic pending Phase 23)")
                # Placeholder: In Phase 23, this would call something like:
                # pickup_system = self.world.systems_manager.get_system(PickupSystem) # or self.world.pickup_system_instance
                # if pickup_system:
                #     pickup_system.pickup_item(action.actor, action.item_id)
                # else:
                #     print(f"[Tick {tick}][ActionExec ERROR] PickupSystem not found for PICKUP action.")


            else:
                logging.warning(f"[Tick {tick}] ActionExec: Unknown action type {type(action)} for actor {getattr(action, 'actor', 'N/A')}; treating as idle.")

__all__ = ["ActionExecutionSystem"]