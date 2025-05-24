from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.systems.combat.damage_types import DamageType


def _setup_world() -> World:
    world = World((10, 10))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    return world


def test_melee_attack_within_range():
    world = _setup_world()
    em = world.entity_manager
    cm = world.component_manager

    attacker = em.create_entity()
    target = em.create_entity()

    cm.add_component(attacker, Position(0, 0))
    cm.add_component(target, Position(1, 0))
    cm.add_component(target, Health(cur=20, max=20))

    combat = CombatSystem(world)
    assert combat.attack(attacker, target, DamageType.MELEE, tick=5)

    hp = cm.get_component(target, Health)
    assert hp.cur == 10
    assert combat.event_log[-1] == {
        "type": "attack",
        "attacker": attacker,
        "target": target,
        "damage": 10,
        "damage_type": DamageType.MELEE.name,
        "tick": 5,
    }


def test_melee_attack_out_of_range():
    world = _setup_world()
    em = world.entity_manager
    cm = world.component_manager

    attacker = em.create_entity()
    target = em.create_entity()

    cm.add_component(attacker, Position(0, 0))
    cm.add_component(target, Position(2, 0))
    cm.add_component(target, Health(cur=15, max=20))

    combat = CombatSystem(world)
    assert not combat.attack(attacker, target, DamageType.MELEE)

    hp = cm.get_component(target, Health)
    assert hp.cur == 15
    assert combat.event_log == []

