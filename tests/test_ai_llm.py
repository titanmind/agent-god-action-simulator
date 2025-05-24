import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from agent_world.ai.llm.cache import LLMCache
from agent_world.ai.llm.llm_manager import LLMManager


def test_lru_cache_eviction():
    cache = LLMCache(capacity=2)
    cache.put("a", "A")
    cache.put("b", "B")
    assert cache.get("a") == "A"
    cache.put("c", "C")
    assert cache.get("b") is None
    assert cache.get("a") == "A"
    assert cache.get("c") == "C"


def test_llm_manager_queue_and_cache():
    manager = LLMManager(cache_size=2, queue_max=2)
    assert manager.request("hello") == "<wait>"
    assert manager.queue.qsize() == 1

    asyncio.run(manager.process_queue_once())
    assert manager.request("hello") == "<wait>"
    assert manager.queue.qsize() == 0
