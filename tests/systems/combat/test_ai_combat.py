from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.role import RoleComponent
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.core.components.known_abilities import KnownAbilitiesComponent
from agent_world.systems.ai.behavior_tree_system import BehaviorTreeSystem
from agent_world.systems.ai.actions import ActionQueue
from agent_world.systems.ai.ai_reasoning_system import RawActionCollector
from agent_world.ai.behaviors.combat_bt import build_combat_tree
from agent_world.systems.combat.damage_types import DamageType
from agent_world.systems.combat.defense import Defense
from agent_world.ai.prompt_builder import build_prompt


def _setup_world(with_spatial: bool = False) -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.action_queue = ActionQueue()
    world.action_queue.enqueue_raw(0, "IDLE")
    world.raw_actions_with_actor = RawActionCollector(world.action_queue)
    if with_spatial:
        world.spatial_index = SpatialGrid(cell_size=1)
    return world


def test_damage_type_enum_extended():
    assert DamageType.FIRE in DamageType
    assert DamageType.MAGIC in DamageType


def test_defense_defaults_include_new_types():
    d = Defense()
    for dt in DamageType:
        assert dt in d.armor and dt in d.dodge


def test_combat_bt_attacks_with_melee():
    world = _setup_world()
    system = BehaviorTreeSystem(world)
    system.register_tree("fighter", build_combat_tree())

    agent = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    cm = world.component_manager
    cm.add_component(agent, AIState(personality="bot"))
    cm.add_component(agent, RoleComponent("fighter", uses_llm=False))
    cm.add_component(agent, Position(1, 1))
    cm.add_component(agent, Health(cur=10, max=10))
    cm.add_component(agent, KnownAbilitiesComponent(["MeleeStrike"]))

    cm.add_component(target, Position(2, 1))
    cm.add_component(target, Health(cur=10, max=10))

    system.update(0)
    world.action_queue.pop()  # discard initial dummy
    queued = world.action_queue.pop()
    from agent_world.systems.ai.actions import UseAbilityAction
    assert isinstance(queued, UseAbilityAction)
    assert queued.actor == agent
    assert queued.ability_name == "MeleeStrike"
    assert queued.target_id == target


def test_combat_bt_retreats_when_low_health():
    world = _setup_world(with_spatial=True)
    system = BehaviorTreeSystem(world)
    system.register_tree("fighter", build_combat_tree())

    agent = world.entity_manager.create_entity()
    enemy = world.entity_manager.create_entity()

    cm = world.component_manager
    cm.add_component(agent, AIState(personality="bot"))
    cm.add_component(agent, RoleComponent("fighter", uses_llm=False))
    cm.add_component(agent, Position(1, 1))
    cm.add_component(agent, Health(cur=2, max=10))
    world.spatial_index.insert(agent, (1, 1))

    cm.add_component(enemy, Position(1, 2))
    cm.add_component(enemy, Health(cur=5, max=5))
    world.spatial_index.insert(enemy, (1, 2))

    system.update(0)
    world.action_queue.pop()
    queued = world.action_queue.pop()
    from agent_world.systems.ai.actions import MoveAction
    assert isinstance(queued, MoveAction)
    assert queued.actor == agent
    assert queued.dx == 0 and queued.dy == -1


def test_prompt_includes_combat_info():
    world = _setup_world()
    agent = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    cm = world.component_manager
    cm.add_component(agent, AIState(personality="bot"))
    cm.add_component(agent, Position(0, 0))
    cm.add_component(agent, Health(cur=8, max=10))
    cm.add_component(target, Position(1, 0))
    cm.add_component(target, Health(cur=4, max=10))

    world.component_manager.add_component(agent, KnownAbilitiesComponent([]))
    # Simple perception: agent sees target
    from agent_world.core.components.perception_cache import PerceptionCache
    world.component_manager.add_component(agent, PerceptionCache(visible=[target], last_tick=0))

    prompt = build_prompt(agent, world)
    assert "combat_info" in prompt
    assert "self_health" in prompt
    assert "nearby_threats" in prompt

