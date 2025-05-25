from agent_world.core.world import World
from agent_world.ai.angel.system import get_angel_system
from agent_world.ai.angel import templates


def test_prompt_builder_stub_callable():
    world = World((5, 5))
    system = get_angel_system(world)
    constraints = templates.get_world_constraints_for_angel()
    scaffolds = templates.get_code_scaffolds_for_angel()
    prompt = system._build_angel_code_generation_prompt(
        "simple fireball ability", constraints, scaffolds
    )
    assert isinstance(prompt, str)

