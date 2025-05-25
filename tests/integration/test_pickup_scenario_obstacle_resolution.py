import os
import asyncio
import socket
import pytest

from agent_world.main import bootstrap
from agent_world.scenarios.default_pickup_scenario import DefaultPickupScenario
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem
from agent_world.ai.llm.llm_manager import LLMManager
from agent_world.systems.movement import pathfinding
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.inventory import Inventory


@pytest.mark.integration
def test_pickup_scenario_obstacle_resolution(monkeypatch, mock_openrouter_api):
    # Force live mode but avoid real network
    monkeypatch.setenv("AW_LLM_MODE", "live")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model")
    monkeypatch.setattr(socket, "gethostbyname", lambda host: "127.0.0.1")

    # speed up reasoning loop for the test
    monkeypatch.setattr(AIReasoningSystem, "COOLDOWN_TICKS", 1)

    async def _sync_llm_request(self, prompt: str, world=None, *, timeout=None, model=None):
        import httpx
        payload = {"model": model or self.model, "messages": [{"role": "user", "content": prompt}]}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers={})
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Patch request before bootstrap so instance uses it
    monkeypatch.setattr(LLMManager, "request", lambda self, *a, **kw: asyncio.get_event_loop().run_until_complete(_sync_llm_request(self, *a, **kw)))

    world = bootstrap(config_path="config.yaml")
    DefaultPickupScenario().setup(world)

    em = world.entity_manager
    cm = world.component_manager
    ids = sorted(em.all_entities.keys())
    agent_id = ids[0] if cm.get_component(ids[0], AIState) else ids[1]
    item_id = ids[1] if agent_id == ids[0] else ids[0]

    obstacle_pos = (world.size[0] // 2, world.size[1] // 2 - 1)

    ability_desc = "remove obstacle"
    ability_class = "RemoveObstacleAbility"
    ability_code = (
        f"from agent_world.systems.movement import pathfinding\n"
        f"pathfinding.OBSTACLES.discard({obstacle_pos})\n"
        f"print('Removed obstacle at {obstacle_pos}')"
    )

    responses = {
        f"Plan steps for agent {agent_id}": [""],
        f"You are Agent {agent_id}": [
            f"GENERATE_ABILITY {ability_desc}",
            f"USE_ABILITY {ability_class}",
            "MOVE N",
            "MOVE N",
            f"PICKUP {item_id}",
        ],
        "Angel LLM responsible": [ability_code],
        "Angel LLM performing": ["PASS"],
    }
    mock_openrouter_api.set_responses_for_agents(responses)

    max_ticks = 10
    for tick in range(max_ticks):
        world.time_manager.tick_counter = tick
        if world.raw_actions_with_actor and world.action_queue is not None:
            for actor, text in world.raw_actions_with_actor:
                world.action_queue.enqueue_raw(actor, text)
            world.raw_actions_with_actor.clear()
        world.systems_manager.update(world, tick)

    assert obstacle_pos not in pathfinding.OBSTACLES
    inv = cm.get_component(agent_id, Inventory)
    assert inv is not None and item_id in inv.items
