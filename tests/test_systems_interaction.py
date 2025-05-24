from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.components.inventory import Inventory
from agent_world.systems.interaction.pickup import PickupSystem, Tag


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
