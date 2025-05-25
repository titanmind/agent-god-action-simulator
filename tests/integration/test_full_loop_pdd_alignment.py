import asyncio
import yaml
import pytest
from agent_world.main import bootstrap
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.core.components.event_log import EventLog
from agent_world.core.components.ai_state import AIState
from agent_world.ai.prompt_builder import build_prompt
from agent_world.persistence.event_log import iter_events, LLM_REQUEST, LLM_RESPONSE


async def _process_prompt(llm, prompt: str) -> str:
    fut = asyncio.get_event_loop().create_future()
    await llm.queue.put((prompt, fut, "pid"))
    await llm.process_queue_item()
    return fut.result()


@pytest.mark.integration
def test_full_loop_pdd_alignment(tmp_path):
    cfg = {
        "world": {"size": [5, 5]},
        "llm": {
            "mode": "offline",
            "agent_decision_model": "agent-test",
            "angel_generation_model": "angel-test",
        },
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg))

    world = bootstrap(config_path=cfg_path)
    world.persistent_event_log_path = tmp_path / "events.json"

    llm = world.llm_manager_instance
    llm.mode = "echo"
    llm.offline = True
    llm.world = world

    em = world.entity_manager
    cm = world.component_manager

    caster = em.create_entity()
    observer = em.create_entity()
    target = em.create_entity()

    cm.add_component(caster, Position(1, 1))
    cm.add_component(observer, Position(3, 1))
    cm.add_component(target, Position(2, 1))
    cm.add_component(target, Health(cur=10, max=10))

    cm.add_component(observer, PerceptionCache(visible=[caster], last_tick=0))
    cm.add_component(observer, EventLog())
    cm.add_component(observer, AIState(personality="t"))

    world.spatial_index.insert_many([
        (caster, (1, 1)),
        (observer, (3, 1)),
        (target, (2, 1)),
    ])

    world.time_manager.tick_counter = 1
    world.ability_system_instance.use("MeleeStrike", caster, target)

    world.systems_manager.update(world, world.time_manager.tick_counter)

    cache = cm.get_component(observer, PerceptionCache)
    log = cm.get_component(observer, EventLog)

    assert cache.visible_ability_uses
    assert log.recent
    event_line = f"- MeleeStrike by {caster}"
    prompt = build_prompt(observer, world)
    assert event_line in prompt

    result = asyncio.run(_process_prompt(llm, prompt))
    assert result

    events = list(iter_events(world.persistent_event_log_path))
    types = [e["event_type"] for e in events]
    assert LLM_REQUEST in types and LLM_RESPONSE in types

    assert world.llm_manager_instance.agent_decision_model == "agent-test"
    assert world.llm_manager_instance.angel_generation_model == "angel-test"

