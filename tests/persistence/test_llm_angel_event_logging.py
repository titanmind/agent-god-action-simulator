import asyncio

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.ai.llm.llm_manager import LLMManager
from agent_world.ai.angel.system import get_angel_system
from agent_world.ai.angel import generator as angel_generator
from agent_world.persistence.event_log import (
    iter_events,
    LLM_REQUEST,
    LLM_RESPONSE,
    ANGEL_ACTION,
)


async def _process_prompt(llm: LLMManager, prompt: str) -> str:
    fut: asyncio.Future[str] = asyncio.get_event_loop().create_future()
    await llm.queue.put((prompt, fut, "pid"))
    await llm.process_queue_item()
    return fut.result()


def test_llm_events_logged(tmp_path):
    world = World((5, 5))
    world.time_manager = TimeManager()
    world.persistent_event_log_path = tmp_path / "log.json"

    llm = LLMManager()
    llm.mode = "echo"
    llm.offline = True
    llm.world = world

    result = asyncio.run(_process_prompt(llm, "say\nhello"))
    assert result == "hello"

    events = list(iter_events(world.persistent_event_log_path))
    assert events[0]["event_type"] == LLM_REQUEST
    assert events[0]["data"]["prompt"] == "say\nhello"
    assert events[1]["event_type"] == LLM_RESPONSE
    assert events[1]["data"]["response"] == "hello"


def test_angel_events_logged(monkeypatch, tmp_path):
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.persistent_event_log_path = tmp_path / "angel.log"

    system = get_angel_system(world)

    # Vault hit path
    system.generate_and_grant(1, "simple fireball ability")
    events = list(iter_events(world.persistent_event_log_path))
    assert any(e["event_type"] == ANGEL_ACTION and e["data"].get("stage") == "vault_hit" for e in events)
    assert any(e["event_type"] == ANGEL_ACTION and e["data"].get("stage") == "granted" for e in events)

    # LLM generation failure path
    def fail_generate(desc: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(angel_generator, "generate_ability", fail_generate)
    system.generate_and_grant(2, "broken ability")

    events = list(iter_events(world.persistent_event_log_path))
    assert any(e["event_type"] == ANGEL_ACTION and e["data"].get("stage") == "failure" for e in events)

