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

import httpx
import yaml
from ...persistence.event_log import (
    append_event,
    LLM_REQUEST,
    LLM_RESPONSE,
)

from .cache import LLMCache


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
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL")

        self.mode = self.current_mode()
        self.is_ready = False # Flag to indicate worker loop is ready

        self.offline = self.mode != "live"
        if self.mode == "live":
            if not self.api_key or not self.model:
                print("[LLMManager] API key or model missing. Forcing offline mode.")
                self.offline = True
                self.mode = "offline" # Explicitly set mode to offline
            else:
                try:
                    # Test connectivity before declaring online
                    socket.gethostbyname("openrouter.ai") 
                    # MODIFIED: Moved print statement to after successful offline check
                except OSError:
                    print("[LLMManager] Network connectivity to openrouter.ai failed. Forcing offline mode.")
                    self.offline = True
                    self.mode = "offline" # Explicitly set mode to offline
        
        if self.offline and self.mode == "live": # If forced offline but config was live
             print(f"[LLMManager] WARNING: LLM mode was 'live' but forced to '{self.mode}' due to missing requirements or network issues.")
        elif not self.offline and self.mode == "live": # Only print if truly online
             print(f"[LLMManager] LLM online: {self.model} (API Key Present: {'Yes' if self.api_key else 'No'})")


        self.cache = LLMCache(capacity=cache_size)
        self.queue: asyncio.Queue[Tuple[str, asyncio.Future[str], str]] = (
            asyncio.Queue(maxsize=queue_max)
        )
        self.loop: asyncio.AbstractEventLoop | None = None
        self._processing_thread: threading.Thread | None = None
        self.world: Any | None = None


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def _add_future_and_queue_request(self, prompt: str, fut: asyncio.Future[str], prompt_id: str, world: Any):
        # This method is executed by call_soon_threadsafe IN THE WORKER THREAD'S LOOP
        world.async_llm_responses[prompt_id] = fut
        try:
            self.queue.put_nowait((prompt, fut, prompt_id))
            # --- MODIFIED LOGGING: Simplified as prompt_builder logs the full prompt ---
            print(f"[LLMManager DEBUG _add_future_and_queue_request] Queued prompt_id {prompt_id}.")
            # --- END MODIFIED LOGGING ---
        except asyncio.QueueFull:
            print(f"[LLMManager ERROR] Queue full. Failed to queue prompt_id {prompt_id}.")
            if world.async_llm_responses.get(prompt_id) == fut:
                world.async_llm_responses.pop(prompt_id, None)
            if not fut.done():
                fut.set_result("<error_llm_queue_full>")

    def request(
        self, prompt: str, world: Any | None = None, timeout: float | None = None
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
            # --- MODIFIED LOGGING: Indication of cache hit ---
            print(f"[LLMManager DEBUG Cache Hit] Returning cached response for prompt (first 70 chars): {prompt[:70].replace(chr(10), '//')}... -> '{cached[:100].replace(chr(10), '//')}'...")
            # --- END MODIFIED LOGGING ---
            return cached

        if not self.is_ready:
            print(f"[LLMManager WARNING] Not ready, returning <wait_llm_not_ready> for prompt: {prompt[:70].replace(chr(10), '//')}...")
            return "<wait_llm_not_ready>"

        if world is None:
            print("[LLMManager ERROR] world is None in live mode request. Cannot manage async future. Returning <error_llm_setup>.")
            return "<error_llm_setup>"
        
        if self.loop is None: 
            print("[LLMManager ERROR] self.loop is None despite is_ready being True. Returning <error_llm_loop_missing>.")
            return "<error_llm_loop_missing>"
        
        fut: asyncio.Future[str] = self.loop.create_future()
        prompt_id = uuid.uuid4().hex
        
        self.loop.call_soon_threadsafe(
            self._add_future_and_queue_request, prompt, fut, prompt_id, world
        )
        return prompt_id


    async def process_queue_item(self) -> None:
        """Handle a single queued prompt and populate the cache."""
        prompt, fut, prompt_id = await self.queue.get()
        # --- MODIFIED LOGGING: Simplified as prompt_builder logs full prompt ---
        print(f"[LLMManager DEBUG process_queue_item] Processing prompt_id {prompt_id} from queue.")
        # --- END MODIFIED LOGGING ---

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
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            
            raw_response_text = None
            try:
                async with httpx.AsyncClient(timeout=15.0) as client: 
                    resp = await client.post(url, json=payload, headers=headers)
                    raw_response_text = resp.text 
                    resp.raise_for_status() 
                    data: Dict[str, Any] = resp.json()

                    # --- MODIFIED LOGGING: Full Raw JSON Response, pretty-printed ---
                    try:
                        parsed_json_for_log = json.loads(raw_response_text) # Use original raw_response_text
                        pretty_raw_response = json.dumps(parsed_json_for_log, indent=2)
                        print(f"\n--- [LLMManager Raw API Response prompt_id {prompt_id}] ---\n{pretty_raw_response}\n--- END Raw API Response ---\n")
                    except json.JSONDecodeError: # Fallback if not valid JSON
                        print(f"\n--- [LLMManager Raw API Response (Non-JSON) prompt_id {prompt_id}] ---\n{raw_response_text}\n--- END Raw API Response ---\n")
                    # --- END MODIFIED LOGGING ---

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
                                    print(f"[LLMManager WARNING] 'content' is not a string or missing in choice for prompt_id {prompt_id}.")
                                    result = "<error_llm_malformed_content>"
                            else:
                                print(f"[LLMManager WARNING] 'message' is not a dict or missing in choice for prompt_id {prompt_id}.")
                                result = "<error_llm_malformed_message>"
                        else:
                            print(f"[LLMManager WARNING] First choice is not a dict for prompt_id {prompt_id}.")
                            result = "<error_llm_malformed_choice>"
                    else:
                        print(f"[LLMManager WARNING] 'choices' array is empty or missing for prompt_id {prompt_id}.")
                        result = "<error_llm_no_choices>"
                    
                    if not result: 
                        print(f"[LLMManager WARNING] LLM returned empty content for prompt_id {prompt_id}.")
                        result = "<llm_empty_response>" 

            except httpx.HTTPStatusError as e:
                print(f"[LLMManager ERROR] HTTP Status Error for prompt_id {prompt_id}: {e.response.status_code} - {e.response.text[:200]}")
                result = f"<error_llm_http_{e.response.status_code}>"
            except httpx.RequestError as e:
                print(f"[LLMManager ERROR] Request Error for prompt_id {prompt_id}: {e}")
                result = "<error_llm_request>"
            except Exception as e: 
                error_type_name = type(e).__name__
                print(f"[LLMManager ERROR] Unexpected error ({error_type_name}) processing LLM response for prompt_id {prompt_id}: {e}")
                if raw_response_text is not None: 
                    print(f"   Raw response (if available): {raw_response_text[:500]}")
                else:
                    print(f"   Raw response was not available (error likely occurred before or during API call).")
                result = "<error_llm_parsing>" 

        # --- MODIFIED LOGGING: Full result string, newlines replaced for console readability ---
        print(f"[LLMManager DEBUG process_queue_item] Result for prompt_id {prompt_id}: '{result.replace(chr(10), '//')}'")
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
            print("[LLMManager INFO] LLM worker_thread event loop started and ready.")
            
            async def _loop_coro() -> None:
                while True:
                    await self.process_queue_item()
            
            try:
                self.loop.run_until_complete(_loop_coro())
            except Exception as e:
                print(f"[LLMManager CRITICAL] LLM worker thread main loop crashed: {e}")
            finally:
                self.is_ready = False
                print("[LLMManager INFO] LLM worker_thread event loop stopped.")

        self._processing_thread = threading.Thread(target=_run, daemon=True, name="LLMProcessingThread")
        self._processing_thread.start()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def current_mode(cls) -> str:
        """Return the configured LLM mode."""
        env_mode = os.getenv("AW_LLM_MODE")
        if env_mode and env_mode.lower() in cls.MODES:
            return env_mode.lower()

        # Try project root config.yaml first
        project_root_config_path = Path("config.yaml")
        if project_root_config_path.exists():
            try:
                with open(project_root_config_path, "r", encoding="utf-8") as fh:
                    cfg = yaml.safe_load(fh) or {}
                mode_from_cfg = str(cfg.get("llm", {}).get("mode", "offline")).lower()
                if mode_from_cfg in cls.MODES:
                    return mode_from_cfg
            except Exception as e: # pylint: disable=broad-except
                print(f"Warning: Error reading project root config.yaml: {e}")
        
        # Fallback to config.yaml relative to this file's location
        path = Path(__file__).resolve().parents[3] / "config.yaml"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    cfg = yaml.safe_load(fh) or {}
                mode_from_cfg = str(cfg.get("llm", {}).get("mode", "offline")).lower()
                if mode_from_cfg in cls.MODES:
                    return mode_from_cfg
            except Exception as e: # pylint: disable=broad-except
                print(f"Warning: Error reading parent config.yaml: {e}")

        return "offline" 

__all__ = ["LLMManager"]