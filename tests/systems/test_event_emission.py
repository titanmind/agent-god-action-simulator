from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.ability.ability_system import AbilitySystem, GLOBAL_ABILITY_EVENT_QUEUE
from agent_world.core.events import AbilityUseEvent


def test_use_emits_event():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    tm = TimeManager()
    tm.tick_counter = 7
    world.time_manager = tm

    system = AbilitySystem(world)

    caster = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    cm = world.component_manager
    cm.add_component(caster, Position(1, 1))
    cm.add_component(target, Position(2, 1))
    cm.add_component(target, Health(cur=10, max=10))

    GLOBAL_ABILITY_EVENT_QUEUE.clear()

    success = system.use("MeleeStrike", caster, target)

    assert success is True
    assert GLOBAL_ABILITY_EVENT_QUEUE
    event = GLOBAL_ABILITY_EVENT_QUEUE[-1]
    assert isinstance(event, AbilityUseEvent)
    assert event.caster_id == caster
    assert event.ability_name == "MeleeStrike"
    assert event.target_id == target
    assert event.tick == 7
