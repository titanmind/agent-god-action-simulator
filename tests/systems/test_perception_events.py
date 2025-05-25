from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.core.components.event_log import EventLog
from agent_world.core.events import AbilityUseEvent
from agent_world.systems.ai.perception_system import EventPerceptionSystem
import agent_world.systems.ability.ability_system as ability_mod


def _setup_world() -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    return world


def test_events_visible_agents_receive(monkeypatch):
    world = _setup_world()

    caster = world.entity_manager.create_entity()
    observer = world.entity_manager.create_entity()
    other = world.entity_manager.create_entity()

    world.component_manager.add_component(observer, PerceptionCache(visible=[caster], last_tick=0))
    world.component_manager.add_component(observer, EventLog())
    world.component_manager.add_component(caster, PerceptionCache(visible=[], last_tick=0))
    world.component_manager.add_component(other, PerceptionCache(visible=[], last_tick=0))
    world.component_manager.add_component(other, EventLog())

    events: list[AbilityUseEvent] = []
    monkeypatch.setattr(ability_mod, "GLOBAL_ABILITY_EVENT_QUEUE", events, False)

    system = EventPerceptionSystem(world)

    events.append(AbilityUseEvent(caster_id=caster, ability_name="Fireball", target_id=None, tick=1))
    system.update(1)

    log_obs = world.component_manager.get_component(observer, EventLog)
    assert log_obs.recent and log_obs.recent[0].ability_name == "Fireball"

    log_other = world.component_manager.get_component(other, EventLog)
    assert not log_other.recent
