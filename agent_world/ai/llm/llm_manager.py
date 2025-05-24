"""LLM request queue and cache manager."""

from __future__ import annotations

import asyncio
import os
import socket
from typing import Tuple

from .cache import LLMCache


class LLMManager:
    """Manage prompt requests through an async queue with caching."""

    def __init__(
        self,
        cache_size: int = 1000,
        queue_max: int = 128,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL")

        self.offline = False
        if not self.api_key or not self.model:
            self.offline = True
        else:
            try:
                socket.gethostbyname("openrouter.ai")
            except OSError:
                self.offline = True

        self.cache = LLMCache(capacity=cache_size)
        self.queue: asyncio.Queue[Tuple[str, asyncio.Future[str]]] = asyncio.Queue(
            maxsize=queue_max
        )

        if not self.offline:
            print(f"LLM online: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def request(self, prompt: str, timeout: float | None = None) -> str:
        """Enqueue ``prompt`` if not cached; return cached response or ``"<wait>"``."""

        cached = self.cache.get(prompt)
        if cached is not None:
            return cached

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover - no running loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        fut: asyncio.Future[str] = loop.create_future()
        try:
            self.queue.put_nowait((prompt, fut))
        except asyncio.QueueFull:
            # Drop the request if the queue is saturated
            return "<wait>"
        return "<wait>"

    async def process_queue_once(self) -> None:
        """Handle a single queued prompt and populate the cache."""

        if self.queue.empty():
            return

        prompt, fut = await self.queue.get()
        result = "<wait>"  # Stubbed response
        self.cache.put(prompt, result)
        if not fut.done():
            fut.set_result(result)
        self.queue.task_done()


__all__ = ["LLMManager"]
