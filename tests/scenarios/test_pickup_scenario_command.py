from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.ai_state import AIState
from agent_world.scenarios.default_pickup_scenario import DefaultPickupScenario
from agent_world.utils.cli import commands
from agent_world.systems.movement.pathfinding import OBSTACLES


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(1)
    return world


def _validate_world(world: World):
    em = world.entity_manager
    cm = world.component_manager
    center_x = world.size[0] // 2
    center_y = world.size[1] // 2

    assert em is not None and cm is not None
    assert len(em.all_entities) == 2
    ids = sorted(em.all_entities.keys())
    ai_state = cm.get_component(ids[0], AIState)
    if ai_state:
        agent_id, item_id = ids[0], ids[1]
    else:
        agent_id, item_id = ids[1], ids[0]
        ai_state = cm.get_component(agent_id, AIState)
    assert ai_state is not None
    assert ai_state.goals == [f"Acquire item {item_id}"]
    assert (center_x, center_y - 1) in OBSTACLES


def test_default_pickup_scenario_setup():
    world = _setup_world()
    DefaultPickupScenario().setup(world)
    _validate_world(world)


def test_scenario_command_executes():
    world = _setup_world()
    commands.scenario(world, "default_pickup")
    _validate_world(world)
