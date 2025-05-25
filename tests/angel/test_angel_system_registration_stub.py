from agent_world.core.world import World
from agent_world.core.systems_manager import SystemsManager
from agent_world.ai.angel.system import AngelSystem, get_angel_system


def test_angel_system_can_register_with_systems_manager():
    world = World((5, 5))
    world.systems_manager = SystemsManager()
    system = get_angel_system(world)
    assert isinstance(system, AngelSystem)
    # Should not raise when registering
    world.register_system(system)
    assert system in list(world.systems_manager)
    # Should not raise when manager dispatches update
    world.systems_manager.update(world, 0)
    # Placeholder method also should be callable directly
    system.process_pending_requests()
