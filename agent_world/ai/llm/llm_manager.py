# agent-god-action-simulator/agent_world/ai/llm/llm_manager.py
"""LLM request queue and cache manager."""

from __future__ import annotations

import asyncio
import os
import socket
import threading
import uuid
from pathlib import Path
from typing import Any, Tuple, Dict
import json # For pretty printing JSON response
import logging

import httpx
from ...config import CONFIG, LLMConfig
from ...persistence.event_log import (
    append_event,
    LLM_REQUEST,
    LLM_RESPONSE,
)

from .cache import LLMCache

logger = logging.getLogger(__name__)


class LLMManager:
    """Manage prompt requests through an async queue with caching."""

    MODES = ("offline", "echo", "live")

    def __init__(
        self,
        cache_size: int = 1000,
        queue_max: int = 128,
        *,
        api_key: str | None = None,
        model: str | None = None,
        agent_decision_model: str | None = None,
        angel_generation_model: str | None = None,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL")

        cfg = llm_config or CONFIG.llm

        self.agent_decision_model = (
            agent_decision_model or cfg.agent_decision_model or self.model
        )
        self.angel_generation_model = (
            angel_generation_model or cfg.angel_generation_model or self.model
        )

        self.mode = self.current_mode(cfg)
        self.is_ready = False # Flag to indicate worker loop is ready

        self.offline = self.mode != "live"
        if self.mode == "live":
            if not self.api_key or not self.model:
                logger.warning("[LLMManager] API key or model missing. Forcing offline mode.")
                self.offline = True
                self.mode = "offline"  # Explicitly set mode to offline
            else:
                try:
                    # Test connectivity before declaring online
                    socket.gethostbyname("openrouter.ai")
                    # MODIFIED: Moved print statement to after successful offline check
                except OSError:
                    logger.warning("[LLMManager] Network connectivity to openrouter.ai failed. Forcing offline mode.")
                    self.offline = True
                    self.mode = "offline" # Explicitly set mode to offline

        if self.offline and self.mode == "live":  # If forced offline but config was live
            logger.warning(
                "[LLMManager] WARNING: LLM mode was 'live' but forced to '%s' due to missing requirements or network issues.",
                self.mode,
            )
        elif not self.offline and self.mode == "live":  # Only log if truly online
            logger.info(
                "[LLMManager] LLM online: %s (API Key Present: %s)",
                self.model,
                "Yes" if self.api_key else "No",
            )


        self.cache = LLMCache(capacity=cache_size)
        self.queue: asyncio.Queue[Tuple[str, asyncio.Future[str], str, str | None]] = (
            asyncio.Queue(maxsize=queue_max)
        )
        self.loop: asyncio.AbstractEventLoop | None = None
        self._processing_thread: threading.Thread | None = None
        self.world: Any | None = None


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def _add_future_and_queue_request(
        self,
        prompt: str,
        fut: asyncio.Future[str],
        prompt_id: str,
        world: Any,
        model: str | None,
    ):
        # This method is executed by call_soon_threadsafe IN THE WORKER THREAD'S LOOP
        world.async_llm_responses[prompt_id] = fut
        try:
            self.queue.put_nowait((prompt, fut, prompt_id, model))
            logger.debug(
                "[LLMManager] Queued prompt_id %s in _add_future_and_queue_request",
                prompt_id,
            )
        except asyncio.QueueFull:
            logger.error("[LLMManager] Queue full. Failed to queue prompt_id %s.", prompt_id)
            if world.async_llm_responses.get(prompt_id) == fut:
                world.async_llm_responses.pop(prompt_id, None)
            if not fut.done():
                fut.set_result("<error_llm_queue_full>")

    def request(
        self,
        prompt: str,
        world: Any | None = None,
        *,
        timeout: float | None = None,
        model: str | None = None,
    ) -> str:
        """Return response prompt_id or result depending on mode."""

        if self.mode == "offline":
            return "<wait>"

        if self.mode == "echo":
            lines = [line.strip() for line in prompt.splitlines() if line.strip()]
            return lines[-1] if lines else ""

        # Live mode
        cached = self.cache.get(prompt)
        if cached is not None:
            logger.debug(
                "[LLMManager] Cache hit for prompt (first 70 chars): %s -> '%s'",
                prompt[:70].replace(chr(10), "//"),
                cached[:100].replace(chr(10), "//"),
            )
            return cached

        if not self.is_ready:
            logger.warning(
                "[LLMManager] Not ready, returning <wait_llm_not_ready> for prompt: %s",
                prompt[:70].replace(chr(10), "//"),
            )
            return "<wait_llm_not_ready>"

        if world is None:
            logger.error(
                "[LLMManager] world is None in live mode request. Cannot manage async future. Returning <error_llm_setup>."
            )
            return "<error_llm_setup>"
        
        if self.loop is None: 
            logger.error(
                "[LLMManager] self.loop is None despite is_ready being True. Returning <error_llm_loop_missing>."
            )
            return "<error_llm_loop_missing>"
        
        fut: asyncio.Future[str] = self.loop.create_future()
        prompt_id = uuid.uuid4().hex
        
        self.loop.call_soon_threadsafe(
            self._add_future_and_queue_request,
            prompt,
            fut,
            prompt_id,
            world,
            model or self.model,
        )
        return prompt_id


    async def process_queue_item(self) -> None:
        """Handle a single queued prompt and populate the cache."""
        item = await self.queue.get()
        if len(item) == 4:
            prompt, fut, prompt_id, model = item
        else:
            prompt, fut, prompt_id = item
            model = self.model
        logger.debug(
            "[LLMManager] Processing prompt_id %s from queue in process_queue_item",
            prompt_id,
        )

        world = getattr(self, "world", None)
        if world is not None:
            dest = getattr(world, "persistent_event_log_path", None)
            if dest is None:
                dest = Path("persistent_events.log")
                world.persistent_event_log_path = dest
            tick = getattr(getattr(world, "time_manager", None), "tick_counter", 0)
            try:
                append_event(dest, tick, LLM_REQUEST, {"prompt_id": prompt_id, "prompt": prompt})
            except Exception:
                pass

        raw_response_text = None
        result = "<wait>"
        if self.offline:
            if self.mode == "echo":
                lines = [ln.strip() for ln in prompt.splitlines() if ln.strip()]
                result = lines[-1] if lines else ""
        else: 
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
            
            raw_response_text = None
            try:
                async with httpx.AsyncClient(timeout=15.0) as client: 
                    resp = await client.post(url, json=payload, headers=headers)
                    raw_response_text = resp.text 
                    resp.raise_for_status() 
                    data: Dict[str, Any] = resp.json()

                    try:
                        parsed_json_for_log = json.loads(raw_response_text)
                        pretty_raw_response = json.dumps(parsed_json_for_log, indent=2)
                        logger.debug(
                            "\n--- [LLMManager Raw API Response prompt_id %s] ---\n%s\n--- END Raw API Response ---\n",
                            prompt_id,
                            pretty_raw_response,
                        )
                    except json.JSONDecodeError:
                        logger.debug(
                            "\n--- [LLMManager Raw API Response (Non-JSON) prompt_id %s] ---\n%s\n--- END Raw API Response ---\n",
                            prompt_id,
                            raw_response_text,
                        )

                    choices = data.get("choices")
                    if choices and isinstance(choices, list) and len(choices) > 0:
                        first_choice = choices[0]
                        if isinstance(first_choice, dict):
                            message = first_choice.get("message")
                            if isinstance(message, dict):
                                content = message.get("content")
                                if isinstance(content, str):
                                    result = content.strip()
                                else:
                                    logger.warning(
                                        "[LLMManager] 'content' is not a string or missing in choice for prompt_id %s.",
                                        prompt_id,
                                    )
                                    result = "<error_llm_malformed_content>"
                            else:
                                logger.warning(
                                    "[LLMManager] 'message' is not a dict or missing in choice for prompt_id %s.",
                                    prompt_id,
                                )
                                result = "<error_llm_malformed_message>"
                        else:
                            logger.warning(
                                "[LLMManager] First choice is not a dict for prompt_id %s.",
                                prompt_id,
                            )
                            result = "<error_llm_malformed_choice>"
                    else:
                        logger.warning(
                            "[LLMManager] 'choices' array is empty or missing for prompt_id %s.",
                            prompt_id,
                        )
                        result = "<error_llm_no_choices>"
                    
                    if not result:
                        logger.warning(
                            "[LLMManager] LLM returned empty content for prompt_id %s.",
                            prompt_id,
                        )
                        result = "<llm_empty_response>"

            except httpx.HTTPStatusError as e:
                logger.error(
                    "[LLMManager] HTTP Status Error for prompt_id %s: %s - %s",
                    prompt_id,
                    e.response.status_code,
                    e.response.text[:200],
                )
                result = f"<error_llm_http_{e.response.status_code}>"
            except httpx.RequestError as e:
                logger.error(
                    "[LLMManager] Request Error for prompt_id %s: %s",
                    prompt_id,
                    e,
                )
                result = "<error_llm_request>"
            except Exception as e:
                error_type_name = type(e).__name__
                logger.error(
                    "[LLMManager] Unexpected error (%s) processing LLM response for prompt_id %s: %s",
                    error_type_name,
                    prompt_id,
                    e,
                )
                if raw_response_text is not None:
                    logger.error("   Raw response (if available): %s", raw_response_text[:500])
                else:
                    logger.error("   Raw response was not available (error likely occurred before or during API call).")
                result = "<error_llm_parsing>"

        # --- MODIFIED LOGGING: Full result string, newlines replaced for console readability ---
        logger.debug(
            "[LLMManager] Result for prompt_id %s: '%s'",
            prompt_id,
            result.replace(chr(10), "//"),
        )
        # --- END MODIFIED LOGGING ---

        if world is not None:
            response_text = raw_response_text if raw_response_text is not None else result
            try:
                append_event(dest, tick, LLM_RESPONSE, {"prompt_id": prompt_id, "response": response_text})
            except Exception:
                pass

        self.cache.put(prompt, result)
        if not fut.done():
            fut.set_result(result)
        self.queue.task_done()

    async def process_queue_once(self) -> None: # Typically not used with the threaded loop
        if self.queue.empty():
            return
        await self.process_queue_item()

    def start_processing_loop(self, world_ref: Any) -> None:
        """Run queue processing in a background thread."""

        self.world = world_ref

        def _run() -> None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.is_ready = True
            logger.info("[LLMManager] LLM worker_thread event loop started and ready.")
            
            async def _loop_coro() -> None:
                while True:
                    await self.process_queue_item()
            
            try:
                self.loop.run_until_complete(_loop_coro())
            except Exception as e:
                logger.critical("[LLMManager] LLM worker thread main loop crashed: %s", e)
            finally:
                self.is_ready = False
                logger.info("[LLMManager] LLM worker_thread event loop stopped.")

        self._processing_thread = threading.Thread(target=_run, daemon=True, name="LLMProcessingThread")
        self._processing_thread.start()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def current_mode(cls, llm_config: LLMConfig | None = None) -> str:
        """Return the configured LLM mode."""
        env_mode = os.getenv("AW_LLM_MODE")
        if env_mode and env_mode.lower() in cls.MODES:
            return env_mode.lower()

        cfg = llm_config or CONFIG.llm
        mode_from_cfg = str(cfg.mode).lower()
        if mode_from_cfg in cls.MODES:
            return mode_from_cfg

        return "offline"

__all__ = ["LLMManager"]
