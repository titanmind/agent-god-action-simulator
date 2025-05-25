
from __future__ import annotations

"""Built-in melee attack ability."""

from typing import Any, Optional

from agent_world.abilities.base import Ability
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.combat.combat_system import CombatSystem


class MeleeStrike(Ability):
    """Basic melee attack targeting the first enemy in range or a specified target."""

    # self.target is now used as a fallback if target_id is not provided to execute/can_use
    # Or it can be set by can_use if no target_id is given.

    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> int:
        return 1 # Cooldown of 1 tick

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
        """Return ``True`` if the specified target or any target is within melee range."""
        if not hasattr(world, "entity_manager") or not hasattr(world, "component_manager"):
            return False
        em = world.entity_manager
        cm = world.component_manager
        
        caster_pos = cm.get_component(caster_id, Position)
        if caster_pos is None:
            return False

        if target_id is not None: # Specific target provided
            if not em.has_entity(target_id): return False
            target_pos = cm.get_component(target_id, Position)
            target_health = cm.get_component(target_id, Health)
            if target_pos is None or target_health is None or target_health.cur <= 0:
                return False
            return CombatSystem._in_melee_range(caster_pos, target_pos)
        else: # Auto-target if no target_id
            for ent_id in list(em.all_entities.keys()):
                if ent_id == caster_id: continue
                
                other_pos = cm.get_component(ent_id, Position)
                other_health = cm.get_component(ent_id, Health)
                if other_pos is None or other_health is None or other_health.cur <= 0:
                    continue
                
                if CombatSystem._in_melee_range(caster_pos, other_pos):
                    return True # Found a potential target
            return False


    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
        """Perform a melee strike against the selected or specified target."""
        if not hasattr(world, "entity_manager") or not hasattr(world, "component_manager"):
            return
        em = world.entity_manager
        cm = world.component_manager

        actual_target_to_attack = target_id

        if actual_target_to_attack is None: # Auto-select if no target_id given
            caster_pos = cm.get_component(caster_id, Position)
            if caster_pos is None: return

            # Find a suitable target if none was provided
            best_candidate = None
            # Basic auto-targeting: first valid entity in range
            for ent_id in list(em.all_entities.keys()):
                if ent_id == caster_id: continue
                other_pos = cm.get_component(ent_id, Position)
                other_health = cm.get_component(ent_id, Health)
                if other_pos and other_health and other_health.cur > 0:
                    if CombatSystem._in_melee_range(caster_pos, other_pos):
                        best_candidate = ent_id
                        break
            actual_target_to_attack = best_candidate

        if actual_target_to_attack is None:
            print(f"[Ability MeleeStrike] Agent {caster_id} could not find a valid target for melee attack.")
            return
        
        # Ensure the final target is valid before attacking
        if not em.has_entity(actual_target_to_attack) or cm.get_component(actual_target_to_attack, Health) is None:
            print(f"[Ability MeleeStrike] Agent {caster_id} target {actual_target_to_attack} became invalid before attack.")
            return

        combat_system = None
        if getattr(world, "systems_manager", None):
            for sys_instance in getattr(world.systems_manager, "_systems", []):
                if isinstance(sys_instance, CombatSystem):
                    combat_system = sys_instance
                    break
        if combat_system is None: # Fallback: create a new one (less ideal)
             print("[Ability MeleeStrike] Warning: CombatSystem not found via SystemsManager, creating new instance.")
             combat_system = CombatSystem(world)
        
        print(f"[Ability MeleeStrike] Agent {caster_id} attacking target {actual_target_to_attack}.")
        combat_system.attack(caster_id, actual_target_to_attack)

__all__ = ["MeleeStrike"]