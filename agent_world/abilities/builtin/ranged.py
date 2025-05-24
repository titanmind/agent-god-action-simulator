
from __future__ import annotations

"""Built-in ranged combat ability."""

from typing import Any, Optional

from agent_world.abilities.base import Ability
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health # Added for target validation
from agent_world.core.components.inventory import Inventory
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.systems.perception.line_of_sight import has_line_of_sight

class ArrowShot(Ability):
    """Shoot the nearest visible target or a specified target and consume one ammo item."""

    def __init__(self, range_val: int = 10) -> None: # Renamed 'range' to 'range_val'
        self.range_val = range_val # Store range value

    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> int:
        return 2 # Cooldown of 2 ticks

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None or not em.has_entity(caster_id):
            return False

        caster_pos = cm.get_component(caster_id, Position)
        inv = cm.get_component(caster_id, Inventory)
        if caster_pos is None or inv is None or not inv.items: # Check for ammo
            return False

        if target_id is not None: # Specific target provided
            if not em.has_entity(target_id): return False
            target_pos = cm.get_component(target_id, Position)
            target_health = cm.get_component(target_id, Health)
            if target_pos is None or target_health is None or target_health.cur <= 0:
                return False
            return has_line_of_sight(caster_pos, target_pos, self.range_val)
        else: # Auto-target if no target_id
            for ent_id in list(em.all_entities.keys()):
                if ent_id == caster_id: continue
                other_pos = cm.get_component(ent_id, Position)
                other_health = cm.get_component(ent_id, Health)
                if other_pos and other_health and other_health.cur > 0:
                    if has_line_of_sight(caster_pos, other_pos, self.range_val):
                        return True # Found a potential target
            return False


    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
        em = getattr(world, "entity_manager", None)
        cm = getattr(world, "component_manager", None)
        if em is None or cm is None or not em.has_entity(caster_id):
            return

        inv = cm.get_component(caster_id, Inventory)
        caster_pos = cm.get_component(caster_id, Position)
        if inv is None or caster_pos is None or not inv.items: # Check for ammo
            print(f"[Ability ArrowShot] Agent {caster_id} cannot use ArrowShot: missing inventory, position, or ammo.")
            return

        actual_target_to_attack = target_id

        if actual_target_to_attack is None: # Auto-select if no target_id given
            # Basic auto-targeting: first valid entity in LOS and range
            for ent_id in list(em.all_entities.keys()):
                if ent_id == caster_id: continue
                other_pos = cm.get_component(ent_id, Position)
                other_health = cm.get_component(ent_id, Health)
                if other_pos and other_health and other_health.cur > 0:
                    if has_line_of_sight(caster_pos, other_pos, self.range_val):
                        actual_target_to_attack = ent_id
                        break
        
        if actual_target_to_attack is None:
            print(f"[Ability ArrowShot] Agent {caster_id} could not find a valid target for ranged attack.")
            return

        # Ensure the final target is valid and in LOS before attacking
        target_pos = cm.get_component(actual_target_to_attack, Position)
        target_health = cm.get_component(actual_target_to_attack, Health)

        if not (em.has_entity(actual_target_to_attack) and 
                target_pos and target_health and target_health.cur > 0 and
                has_line_of_sight(caster_pos, target_pos, self.range_val)):
            print(f"[Ability ArrowShot] Agent {caster_id} target {actual_target_to_attack} became invalid or out of LOS before attack.")
            return

        inv.items.pop(0) # Consume one ammo

        combat_system = None
        if hasattr(world, 'systems_manager'): 
            for sys_instance in world.systems_manager._systems:
                if isinstance(sys_instance, CombatSystem):
                    combat_system = sys_instance
                    break
        if combat_system is None: 
             print("[Ability ArrowShot] Warning: CombatSystem not found via SystemsManager, creating new instance.")
             combat_system = CombatSystem(world) # Pass world here

        print(f"[Ability ArrowShot] Agent {caster_id} shooting at target {actual_target_to_attack}.")
        combat_system.attack(caster_id, actual_target_to_attack) # Default damage type is MELEE, can specify if ranged has own type

__all__ = ["ArrowShot"]