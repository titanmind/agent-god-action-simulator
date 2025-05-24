from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.components.inventory import Inventory
from agent_world.systems.interaction.pickup import PickupSystem, Tag
from agent_world.systems.interaction.trading import TradingSystem
from agent_world.systems.interaction.stealing import StealingSystem, Relationship


def test_pickup_moves_item_to_inventory():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()

    player = world.entity_manager.create_entity()
    item = world.entity_manager.create_entity()

    world.component_manager.add_component(player, Position(1, 1))
    world.component_manager.add_component(player, Inventory(capacity=2))

    world.component_manager.add_component(item, Position(1, 1))
    world.component_manager.add_component(item, Tag("item"))

    system = PickupSystem(world)
    system.update()

    inv = world.component_manager.get_component(player, Inventory)
    assert inv.items == [item]
    assert not world.entity_manager.has_entity(item)


def test_pickup_respects_capacity():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()

    player = world.entity_manager.create_entity()
    item1 = world.entity_manager.create_entity()
    item2 = world.entity_manager.create_entity()

    world.component_manager.add_component(player, Position(0, 0))
    world.component_manager.add_component(player, Inventory(capacity=1))

    world.component_manager.add_component(item1, Position(0, 0))
    world.component_manager.add_component(item1, Tag("item"))

    world.component_manager.add_component(item2, Position(0, 0))
    world.component_manager.add_component(item2, Tag("item"))

    system = PickupSystem(world)
    system.update()

    inv = world.component_manager.get_component(player, Inventory)
    assert inv.items == [item1]
    assert not world.entity_manager.has_entity(item1)
    assert world.entity_manager.has_entity(item2)


def test_trading_swaps_items():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()

    a = world.entity_manager.create_entity()
    b = world.entity_manager.create_entity()
    item_a = world.entity_manager.create_entity()
    item_b = world.entity_manager.create_entity()

    world.component_manager.add_component(a, Position(0, 0))
    world.component_manager.add_component(b, Position(0, 0))
    world.component_manager.add_component(a, Inventory(capacity=2))
    world.component_manager.add_component(b, Inventory(capacity=2))

    cm = world.component_manager
    cm.get_component(a, Inventory).items.append(item_a)
    cm.get_component(b, Inventory).items.append(item_b)

    system = TradingSystem(world)
    system.update()

    inv_a = cm.get_component(a, Inventory)
    inv_b = cm.get_component(b, Inventory)
    assert inv_a.items == [item_b]
    assert inv_b.items == [item_a]


def test_stealing_penalizes_reputation():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()

    thief = world.entity_manager.create_entity()
    victim = world.entity_manager.create_entity()
    item = world.entity_manager.create_entity()

    world.component_manager.add_component(thief, Position(1, 1))
    world.component_manager.add_component(victim, Position(1, 1))
    world.component_manager.add_component(thief, Inventory(capacity=1))
    world.component_manager.add_component(victim, Inventory(capacity=1))
    world.component_manager.add_component(thief, Relationship(reputation=5))
    world.component_manager.add_component(victim, Relationship(reputation=5))

    cm = world.component_manager
    cm.get_component(victim, Inventory).items.append(item)

    system = StealingSystem(world, penalty=2)
    system.update()

    inv_thief = cm.get_component(thief, Inventory)
    rel_thief = cm.get_component(thief, Relationship)
    inv_victim = cm.get_component(victim, Inventory)

    assert inv_thief.items == [item]
    assert inv_victim.items == []
    assert rel_thief.reputation == 3
