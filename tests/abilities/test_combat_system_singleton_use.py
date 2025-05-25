from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.systems_manager import SystemsManager
from agent_world.systems.ability.ability_system import AbilitySystem
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.core.components.inventory import Inventory


def _setup_world(with_singleton: bool = True) -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.systems_manager = SystemsManager()
    combat = CombatSystem(world)
    world.systems_manager.register(combat)
    if with_singleton:
        world.combat_system_instance = combat
    return world


def _add_basic_entities(world: World, with_inventory: bool = False) -> tuple[int, int]:
    em = world.entity_manager
    cm = world.component_manager
    caster = em.create_entity()
    target = em.create_entity()
    cm.add_component(caster, Position(1, 1))
    cm.add_component(target, Position(2, 1))
    cm.add_component(target, Health(cur=10, max=10))
    if with_inventory:
        cm.add_component(caster, Inventory(capacity=1, items=["arrow"]))
    return caster, target


def test_melee_strike_uses_existing_combat_system():
    world = _setup_world(True)
    ability_sys = AbilitySystem(world)
    caster, target = _add_basic_entities(world)

    combat_before = world.combat_system_instance
    assert combat_before is not None

    ability_sys.use("MeleeStrike", caster, target)

    assert world.combat_system_instance is combat_before
    assert any(evt["attacker"] == caster for evt in combat_before.event_log)


def test_arrow_shot_uses_existing_combat_system_via_manager():
    world = _setup_world(False)
    ability_sys = AbilitySystem(world)
    caster, target = _add_basic_entities(world, with_inventory=True)

    combat_from_manager = next(
        s for s in world.systems_manager._systems if isinstance(s, CombatSystem)
    )

    ability_sys.use("ArrowShot", caster, target)

    # ArrowShot should not instantiate a new CombatSystem
    assert world.combat_system_instance in (None, combat_from_manager)
    assert combat_from_manager.event_log
    attack_event = next(
        evt for evt in combat_from_manager.event_log if evt.get("type") == "attack"
    )
    assert attack_event["attacker"] == caster and attack_event["target"] == target
