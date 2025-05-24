from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.role import RoleComponent
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.ai.behavior_tree_system import BehaviorTreeSystem
from agent_world.ai.behaviors.creature_bt import build_creature_tree


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.raw_actions_with_actor = []
    return world


def test_creature_attacks_when_adjacent():
    world = _setup_world()
    system = BehaviorTreeSystem(world)
    system.register_tree("creature", build_creature_tree())

    creature = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    cm = world.component_manager
    cm.add_component(creature, AIState(personality="beast"))
    cm.add_component(creature, RoleComponent("creature", uses_llm=False))
    cm.add_component(creature, Position(1, 1))

    cm.add_component(target, Position(2, 1))
    cm.add_component(target, Health(cur=10, max=10))

    system.update(0)

    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor[0]
    assert actor == creature
    assert action == f"USE_ABILITY MeleeStrike {target}"


def test_default_tree_used_for_other_roles():
    world = _setup_world()
    system = BehaviorTreeSystem(world)
    system.register_tree("creature", build_creature_tree())

    merchant = world.entity_manager.create_entity()
    cm = world.component_manager
    cm.add_component(merchant, AIState(personality="m"))
    cm.add_component(merchant, RoleComponent("merchant", uses_llm=False))
    cm.add_component(merchant, Position(0, 0))

    system.update(0)

    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor[0]
    assert actor == merchant
    assert action.startswith("MOVE")

