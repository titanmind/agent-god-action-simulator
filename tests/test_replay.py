from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.persistence.replay import replay


def _make_world() -> World:
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    w.time_manager = TimeManager()
    em = w.entity_manager
    cm = w.component_manager
    attacker = em.create_entity()
    target = em.create_entity()
    cm.add_component(attacker, Position(0, 0))
    cm.add_component(target, Position(1, 0))
    cm.add_component(target, Health(cur=20, max=20))
    return w


def test_replay_attack_event_determinism():
    world = _make_world()
    em = world.entity_manager
    cm = world.component_manager

    combat = CombatSystem(world)
    combat.attack(1, 2, tick=1)
    log = list(combat.event_log)

    def world_factory() -> World:
        return _make_world()

    new_world, same = replay(world_factory, log)
    assert same
    hp = new_world.component_manager.get_component(2, Health)
    assert hp.cur == 10
