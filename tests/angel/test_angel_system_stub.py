from agent_world.core.world import World
from agent_world.ai.angel.system import AngelSystem, get_angel_system


def test_angel_system_stub_instance_on_world():
    world = World((5, 5))
    system1 = get_angel_system(world)
    assert isinstance(system1, AngelSystem)
    assert getattr(world, "angel_system_instance") is system1
    system2 = get_angel_system(world)
    assert system1 is system2
    assert system1.generate_and_grant(1, "do something") == {"status": "stub"}
