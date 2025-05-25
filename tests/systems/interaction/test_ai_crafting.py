from pathlib import Path
from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.ai_state import AIState, Goal
from agent_world.core.components.inventory import Inventory
from agent_world.core.components.role import RoleComponent
from agent_world.core.components.position import Position
from agent_world.systems.interaction.crafting import CraftingSystem
from agent_world.systems.interaction.pickup import PickupSystem, Tag
from agent_world.systems.ai.behavior_tree import BehaviorTree, Action


def _setup_world() -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.spatial_index = SpatialGrid(cell_size=1)
    return world


def test_agent_gathers_and_crafts(tmp_path):
    world = _setup_world()
    recipe_path = Path(__file__).resolve().parents[3] / 'agent_world' / 'data' / 'recipes.json'
    crafting = CraftingSystem(world, recipe_path=recipe_path)
    world.crafting_system = crafting
    pickup_sys = PickupSystem(world)

    agent = world.entity_manager.create_entity()
    cm = world.component_manager
    cm.add_component(agent, AIState(personality='bot', goals=[Goal('craft', 'double')], known_recipes=['double']))
    cm.add_component(agent, RoleComponent('crafter', uses_llm=False))
    cm.add_component(agent, Inventory(capacity=5))
    cm.add_component(agent, Position(0, 0))
    world.spatial_index.insert(agent, (0, 0))

    item1 = world.entity_manager.create_entity()
    item2 = world.entity_manager.create_entity()
    for item in (item1, item2):
        cm.add_component(item, Position(0, 0))
        cm.add_component(item, Tag('item'))
        world.spatial_index.insert(item, (0, 0))

    # Gather resources
    pickup_sys.update()
    inv = cm.get_component(agent, Inventory)
    assert len(inv.items) == 2

    def craft_action(aid: int, w: World):
        ai = cm.get_component(aid, AIState)
        inv_comp = cm.get_component(aid, Inventory)
        craft_sys = getattr(w, 'crafting_system', None)
        if ai and inv_comp and craft_sys and ai.goals:
            goal = ai.goals[0]
            if goal.type == 'craft' and goal.target in ai.known_recipes:
                if craft_sys.craft(aid, goal.target):
                    ai.goals.pop(0)
                    return 'LOG crafted'
        return None

    tree = BehaviorTree(Action(craft_action))

    # Craft
    tree.run(agent, world)

    inv = cm.get_component(agent, Inventory)
    assert len(inv.items) == 1
    assert cm.get_component(agent, AIState).goals == []
