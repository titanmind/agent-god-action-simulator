from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.ability.ability_system import AbilitySystem


def test_melee_strike_attacks_and_cooldown():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()

    attacker = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    cm = world.component_manager
    cm.add_component(attacker, Position(0, 0))
    cm.add_component(target, Position(1, 0))
    cm.add_component(target, Health(cur=20, max=20))

    system = AbilitySystem(world)
    assert system.use("MeleeStrike", attacker)
    hp = cm.get_component(target, Health)
    assert hp.cur == 10

    assert not system.use("MeleeStrike", attacker)
    system.update()
    assert system.use("MeleeStrike", attacker)
    hp = cm.get_component(target, Health)
    assert hp.cur == 0
