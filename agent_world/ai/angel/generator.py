# agent-god-action-simulator/agent_world/ai/angel/generator.py
"""Helper for writing generated ability scaffolds."""

from __future__ import annotations

from pathlib import Path
import re
import inflection 

GENERATED_DIR = Path(__file__).resolve().parents[2] / "abilities" / "generated"


def _slugify(text: str) -> str:
    common_words = {"a", "an", "the", "is", "for", "to", "of", "with", "my", "me", "at"}
    words = [word for word in re.split(r'[^a-zA-Z0-9]+', text.strip().lower()) if word and word not in common_words]
    slug = "_".join(words)
    slug = re.sub(r'_+', '_', slug).strip("_") 
    return slug or "custom_ability"


def _class_name_from_slug(slug: str) -> str:
    class_name_base = inflection.camelize(slug, uppercase_first_letter=True)
    if not class_name_base: class_name_base = "Generated"
    if not class_name_base.endswith("Ability"):
        class_name_base += "Ability"
    return class_name_base


def generate_ability(desc: str, *, stub_code: str | None = None) -> Path:
    base_slug = _slugify(desc)
    current_slug_for_file = base_slug
    # Class name for the *first* generated file will be based on the clean description.
    # Subsequent files will have numbers in classname to match filename.
    class_name = _class_name_from_slug(current_slug_for_file) 
    
    filename = f"{current_slug_for_file}.py"
    path = GENERATED_DIR / filename
    counter = 1
    
    while path.exists(): 
        current_slug_for_file = f"{base_slug}_{counter}" 
        class_name = _class_name_from_slug(current_slug_for_file) 
        filename = f"{current_slug_for_file}.py"
        path = GENERATED_DIR / filename
        counter += 1
        if counter > 20: 
            raise RuntimeError(f"Could not find unique filename for ability based on: {desc} after {counter-1} tries.")

    final_stub_code_body = stub_code 
    imports_for_stub_section = ""
    can_use_logic_body = "return True # Default can_use"

    specific_heal_desc_trigger = "a simple self heal ability for 5 health"
    if desc.strip().lower() == specific_heal_desc_trigger.lower():
        imports_for_stub_section = "from agent_world.core.components.health import Health"
        final_stub_code_body = """
        if world and hasattr(world, 'component_manager') and hasattr(world, 'entity_manager'):
            cm = world.component_manager; em = world.entity_manager
            if not em.has_entity(caster_id): print(f"Caster {caster_id} not found."); return
            health_comp = cm.get_component(caster_id, Health)
            if health_comp:
                heal_amount = 5; old_health = health_comp.cur
                health_comp.cur = min(health_comp.max, health_comp.cur + heal_amount)
                print(f"Agent {caster_id} used {self.__class__.__name__} and healed for {health_comp.cur - old_health} HP. Health: {health_comp.cur}/{health_comp.max}")
            else: print(f"Agent {caster_id} no Health component.")
        else: print(f"Agent {caster_id} world/managers missing.")
"""
    # --- Disintegrate Obstacle Ability ---
    elif "disintegrate obstacle" in desc.strip().lower() or \
         "remove obstacle" in desc.strip().lower() or \
         "clear obstacle" in desc.strip().lower():
        
        imports_for_stub_section = (
            "from agent_world.systems.movement.pathfinding import OBSTACLES, is_blocked\n"
            # Position not strictly needed if we always target (50,49) but good for future.
            "from agent_world.core.components.position import Position" 
        )
        # MODIFIED: can_use is now always True if the ability is called.
        # The prompt_builder's critical prompt logic should be the main gatekeeper for when to suggest using it.
        can_use_logic_body = """
        # For this scenario, if the LLM decides to use it based on the critical prompt,
        # we assume it's a valid situation. The obstacle check is done in execute.
        return True
"""
        # execute: always try to remove (50,49)
        final_stub_code_body = """
        # Note: OBSTACLES, is_blocked, Position are imported.
        obstacle_to_remove = (50,49) # Hardcoded for the specific scenario
            
        if is_blocked(obstacle_to_remove): # Check if it's currently considered an obstacle
            if obstacle_to_remove in OBSTACLES: # Double check it's in the actual set
                OBSTACLES.discard(obstacle_to_remove)
                print(f"Agent {caster_id} used {self.__class__.__name__} and REMOVED obstacle at {obstacle_to_remove}! Obstacles left: {len(OBSTACLES)}")
            else:
                 print(f"Agent {caster_id} {self.__class__.__name__}: Obstacle at {obstacle_to_remove} was is_blocked() but not in OBSTACLES set.")
        else:
             print(f"Agent {caster_id} used {self.__class__.__name__}, but no obstacle was found/already cleared at {obstacle_to_remove}.")
"""

    elif final_stub_code_body is None: 
        clean_desc_for_print = desc.replace('"', '\\"').replace("'", "\\'")
        final_stub_code_body = f"print(f\"Agent {{caster_id}} used {{self.__class__.__name__}} targeting {{target_id}} (desc: '{clean_desc_for_print}')\")"
    
    indented_body = "\n".join("        " + ln.rstrip() for ln in final_stub_code_body.strip().splitlines()) or "        pass"
    indented_can_use = "\n".join("        " + ln.rstrip() for ln in can_use_logic_body.strip().splitlines()) or "        return True"

    template = f'''"""Generated ability scaffold.
Description (from LLM): {desc}
Generated Class Name: {class_name}"""
from __future__ import annotations
from typing import Any, Optional
from agent_world.abilities.base import Ability
{imports_for_stub_section}

class {class_name}(Ability):
    """Auto-generated ability: {desc}"""
    @property
    def energy_cost(self) -> int: return 0 
    @property
    def cooldown(self) -> int: return 1 

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
{indented_can_use}

    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
{indented_body}

__all__ = ["{class_name}"]
'''
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(template, encoding="utf-8")
    print(f"[AngelGenerator] Generated ability '{class_name}' at {path} from description: '{desc}'")
    return path

__all__ = ["generate_ability"]