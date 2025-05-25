from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.core.components.inventory import Inventory
from agent_world.persistence.event_log import (
    iter_events,
    COMBAT_ATTACK,
    COMBAT_DEATH,
    CRAFT,
)
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.systems.interaction.crafting import CraftingSystem


def test_combat_and_crafting_logged(tmp_path):
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.persistent_event_log_path = tmp_path / "events.json"

    combat = CombatSystem(world)
    crafting = CraftingSystem(world)

    em = world.entity_manager
    cm = world.component_manager

    attacker = em.create_entity()
    target = em.create_entity()
    cm.add_component(attacker, Position(1, 1))
    cm.add_component(target, Position(1, 2))
    cm.add_component(target, Health(cur=10, max=10))

    world.time_manager.tick_counter = 1
    combat.attack(attacker, target)

    crafter = em.create_entity()
    item = em.create_entity()
    cm.add_component(crafter, Inventory(capacity=5, items=[item]))
    world.time_manager.tick_counter = 2
    crafting.craft(crafter, "basic")

    events = list(iter_events(world.persistent_event_log_path))
    types = [e["event_type"] for e in events]
    assert COMBAT_ATTACK in types
    assert COMBAT_DEATH in types
    assert CRAFT in types
