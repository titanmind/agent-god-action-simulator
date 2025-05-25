from agent_world.core.world import World
from agent_world.ai.angel.system import get_angel_system, run_in_sandbox


def test_conceptual_test_stub_callable():
    world = World((5, 5))
    system = get_angel_system(world)
    assert callable(run_in_sandbox)
    result = system._conceptual_test_generated_code("print('hi')", "dummy")
    assert result is True
