from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.event_log import EventLog
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.core.events import AbilityUseEvent
from agent_world.ai.prompt_builder import build_prompt


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    return world


def test_prompt_uses_visible_ability_uses():
    world = _setup_world()
    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="t"))

    event = AbilityUseEvent(caster_id=2, ability_name="Fireball", target_id=None, tick=1)
    cache = PerceptionCache(visible=[], visible_ability_uses=[event], last_tick=0)
    world.component_manager.add_component(agent_id, cache)
    # Ensure EventLog is present but empty to confirm source
    world.component_manager.add_component(agent_id, EventLog())

    prompt = build_prompt(agent_id, world)

    assert "Recent Events:" in prompt
    assert "- Fireball by 2" in prompt

