from agent_world.core.world import World
from agent_world.ai.angel.system import get_angel_system
from agent_world.ai.angel import templates


def _setup():
    world = World((5, 5))
    system = get_angel_system(world)
    constraints = templates.get_world_constraints_for_angel()
    scaffolds = templates.get_code_scaffolds_for_angel()
    return system, constraints, scaffolds


def test_prompt_contains_description_and_constraints():
    system, constraints, scaffolds = _setup()
    desc = "healing aura"
    prompt = system._build_angel_code_generation_prompt(desc, constraints, scaffolds)
    assert desc in prompt
    assert "ability_base_methods" in prompt
    for method in constraints["ability_base_methods"]:
        assert method in prompt


def test_prompt_includes_scaffold_snippets():
    system, constraints, scaffolds = _setup()
    prompt = system._build_angel_code_generation_prompt("simple ability", constraints, scaffolds)
    assert scaffolds["imports"] in prompt
    assert "class {class_name}(Ability)" in prompt
