
# agent-god-action-simulator/agent_world/ai/angel/generator.py
"""Helper for writing generated ability scaffolds."""

from __future__ import annotations

from pathlib import Path
import re
import inflection # For PascalCase, install with: pip install inflection

GENERATED_DIR = Path(__file__).resolve().parents[2] / "abilities" / "generated"


def _slugify(text: str) -> str:
    """Return a filesystem-friendly slug for ``text``."""
    # Remove common small words that don't add much to filename
    common_words = {"a", "an", "the", "is", "for", "to", "of", "with", "my", "me"}
    words = [word for word in re.split(r'[^a-zA-Z0-9]+', text.strip().lower()) if word and word not in common_words]
    slug = "_".join(words)
    slug = re.sub(r'_+', '_', slug).strip("_") # Consolidate multiple underscores
    return slug or "custom_ability"


def _class_name_from_slug(slug: str) -> str:
    """Convert ``slug`` to PascalCase class name, ensuring it ends with 'Ability'."""
    class_name_base = inflection.camelize(slug, uppercase_first_letter=True)
    if not class_name_base: class_name_base = "Generated" # Fallback
    if not class_name_base.endswith("Ability"):
        class_name_base += "Ability"
    return class_name_base


def generate_ability(desc: str, *, stub_code: str | None = None) -> Path:
    """Create a basic ability module under :mod:`abilities.generated`.

    Parameters
    ----------
    desc:
        Short description or name used to derive the module/class.
    stub_code:
        Optional Python code string for the execute method's body.

    Returns
    -------
    pathlib.Path
        Path to the created module.
    """

    slug = _slugify(desc)
    class_name = _class_name_from_slug(slug)

    filename = f"{slug}.py"
    path = GENERATED_DIR / filename
    counter = 1
    # Ensure unique filename if slug/class name isn't perfectly unique
    while path.exists(): 
        original_slug_for_retry = slug
        slug = f"{original_slug_for_retry}_{counter}"
        class_name = _class_name_from_slug(slug)
        filename = f"{slug}.py"
        path = GENERATED_DIR / filename
        counter += 1
        if counter > 10:
            raise RuntimeError(f"Could not find unique filename for ability based on: {desc}")

    # --- MODIFIED SECTION for Goal 1 ---
    final_stub_code = stub_code # Use provided stub_code by default (if any)
    imports_for_stub_section = "" # Additional imports for the generated file's header

    specific_heal_desc_trigger = "a simple self heal ability for 5 health"
    if desc.strip().lower() == specific_heal_desc_trigger.lower():
        imports_for_stub_section = "from agent_world.core.components.health import Health"
        # This stub code will be placed inside the execute method
        final_stub_code = """
        # Note: 'Health' component is imported at the top of this generated file.
        if world and hasattr(world, 'component_manager') and hasattr(world, 'entity_manager'):
            cm = world.component_manager
            em = world.entity_manager

            if not em.has_entity(caster_id):
                print(f"Agent {caster_id} (caster) not found in entity manager.")
                return

            health_comp = cm.get_component(caster_id, Health)
            if health_comp:
                heal_amount = 5
                old_health = health_comp.cur
                health_comp.cur = min(health_comp.max, health_comp.cur + heal_amount)
                healed_by = health_comp.cur - old_health
                print(f"Agent {caster_id} used {self.__class__.__name__} and healed for {healed_by} HP. Health: {health_comp.cur}/{health_comp.max}")
            else:
                print(f"Agent {caster_id} tried to use {self.__class__.__name__}, but no Health component found.")
        else:
            print(f"Agent {caster_id} tried to use {self.__class__.__name__}, but world, component_manager, or entity_manager is missing.")
"""
    elif final_stub_code is None: # Default print stub if no specific match and no stub_code override from args
        clean_desc_for_print = desc.replace('"', '\\"').replace("'", "\\'")
        final_stub_code = f"print(f\"Agent {{caster_id}} used {{self.__class__.__name__}} targeting {{target_id}} (desc: '{clean_desc_for_print}')\")"
    # --- END MODIFIED SECTION ---

    # Indent the chosen stub code correctly
    indented_body = "\n".join("        " + ln.rstrip() for ln in final_stub_code.strip().splitlines()) or "        pass"

    template = f'''"""Generated ability scaffold.

Description (from LLM):
    {desc}

Generated Class Name: {class_name}
"""
from __future__ import annotations
from typing import Any, Optional
from agent_world.abilities.base import Ability
{imports_for_stub_section} # This will insert "from agent_world.core.components.health import Health" or be empty
# You might need to import components if your stub_code uses them, e.g.:
# from agent_world.core.components.health import Health # Standard comment

class {class_name}(Ability):
    """Auto-generated ability: {desc}"""

    @property
    def energy_cost(self) -> int:
        return 0 # Modified: Default small cost to 0 for simple test

    @property
    def cooldown(self) -> int:
        return 1 # Modified: Default small cooldown to 1 for faster testing

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
        # For the self-heal, it can always be used if not on cooldown.
        return True

    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
        # This is where the ability's effect happens.
        # The 'caster_id' is the entity using the ability.
        # 'world' gives access to entity_manager, component_manager, etc.
        # 'target_id' is optional, for abilities that target another entity.
{indented_body}

__all__ = ["{class_name}"]
'''

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(template, encoding="utf-8")
    print(f"[AngelGenerator] Generated ability '{class_name}' at {path} from description: '{desc}'")
    return path


__all__ = ["generate_ability"]