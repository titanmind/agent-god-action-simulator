
# agent_world/ai/angel/system.py
"""Angel system for granting new abilities."""

from __future__ import annotations

from typing import Any, Dict, Optional # Added Optional
from pathlib import Path
import logging
import re
import time 

from . import generator as angel_generator
from . import templates
from .vault_index import get_vault_index
from ...core.components.known_abilities import KnownAbilitiesComponent
from ...core.components.ai_state import AIState
from ...persistence.event_log import append_event, ANGEL_ACTION

logger = logging.getLogger(__name__)

ANGEL_LLM_REQUEST_TIMEOUT_SECONDS = 20.0 


class AngelSystem:
    """Generate abilities via Vault lookup or LLM."""

    def __init__(self, world: Any) -> None:
        self.world = world
        self.request_queue: list[tuple[int, str, str | None, str | None, Dict[str, Any] | None]] = [] 
        self.current_processing_request: tuple[int, str, str | None, str | None, Dict[str, Any] | None] | None = None
        self.current_processing_stage: str | None = None 

    def update(self, world: Any, tick: int) -> None:
        if not self.world.paused_for_angel and self.current_processing_request:
            logger.warning("[AngelSystem] World unpaused but a request was mid-processing. Clearing state.")
            agent_id_stuck, desc_stuck, _, _, ctx_stuck = self.current_processing_request
            self._finalize_request_processing(agent_id_stuck, desc_stuck, ctx_stuck, {"status": "failure", "reason": "Angel processing interrupted or timed out by main loop"})
            self.current_processing_request = None
            self.current_processing_stage = None

    def queue_request(self, agent_id: int, description: str, step_context: Optional[Dict[str, Any]] = None) -> dict:
        if not description:
            logger.error("[AngelSystem] Attempted to queue ability generation with empty description for agent %s.", agent_id)
            return {"status": "failure", "reason": "Empty description"}
        
        self.request_queue.append((agent_id, description, None, None, step_context)) 
        logger.info("[AngelSystem] Queued ability request for agent %s: '%s'. Context: %s. Queue size: %s", agent_id, description, step_context, len(self.request_queue))
        return {"status": "queued"}

    def _finalize_request_processing(self, agent_id: int, description: str, original_step_context: Optional[Dict[str, Any]], result: dict) -> None:
        cm = getattr(self.world, "component_manager", None)
        ai_state = cm.get_component(agent_id, AIState) if cm else None

        if ai_state:
            ai_state.waiting_for_ability_generation_desc = None 
            ai_state.needs_immediate_rethink = True
            if result.get("status") == "success":
                ai_state.newly_generated_ability_name = result.get("ability_class_name")
                ai_state.newly_generated_ability_context = original_step_context 
                ai_state.last_error = None 
            else: # Failure
                ai_state.last_error = result.get("reason", "Unknown Angel System error")
                # Task 7.3: If generation failed, increment retry for the original plan step if context matches
                # This logic is now primarily handled in AIReasoningSystem when it sees last_error is set.
                # AngelSystem just provides the error. AIReasoningSystem owns plan step retries.
                # However, setting last_error here is the trigger.
                logger.warning("[AngelSystem] Ability generation FAILED for agent %s. Reason: %s. Error set on AIState.", agent_id, ai_state.last_error)


            logger.info("[AngelSystem] Finalized request for agent %s (Desc: '%s'). Result: %s. Needs rethink.", agent_id, description, result.get("status"))


    def _get_llm_response_blocking(self, prompt_id: str, timeout: float) -> str | None:
        if not hasattr(self.world, "async_llm_responses"): return None
        future = self.world.async_llm_responses.get(prompt_id)
        if not future: 
            logger.error("[AngelSystem] LLM Future not found for prompt_id %s", prompt_id)
            return f"<error_llm_future_not_found_{prompt_id}>"

        start_time = time.time()
        while not future.done():
            if time.time() - start_time > timeout:
                logger.warning("[AngelSystem] Timeout waiting for LLM future %s", prompt_id)
                self.world.async_llm_responses.pop(prompt_id, None) 
                return "<error_llm_timeout>" 
            time.sleep(0.05) 

        try: response_text = future.result()
        except Exception as e:
            logger.error("[AngelSystem] Error getting result from LLM future %s: %s", prompt_id, e)
            response_text = f"<error_llm_future_exception_{type(e).__name__}>"
        
        self.world.async_llm_responses.pop(prompt_id, None) 
        return response_text

    def process_pending_requests(self) -> None:
        if not self.world.paused_for_angel: return 

        llm = getattr(self.world, "llm_manager_instance", None)
        if not llm:
            logger.error("[AngelSystem] LLMManager not found. Cannot process ability generation.")
            while self.request_queue:
                agent_id, desc, _, _, ctx = self.request_queue.pop(0)
                self._finalize_request_processing(agent_id, desc, ctx, {"status":"failure", "reason":"LLMManager unavailable"})
            if self.current_processing_request:
                agent_id, desc, _, _, ctx = self.current_processing_request
                self._finalize_request_processing(agent_id, desc, ctx, {"status":"failure", "reason":"LLMManager unavailable during processing"})
                self.current_processing_request = None
            self.world.paused_for_angel = False
            return

        if self.current_processing_request:
            agent_id, description, pending_llm_id, gen_code, orig_ctx = self.current_processing_request
            
            if self.current_processing_stage == "code_generation" and pending_llm_id:
                actual_generated_code = self._get_llm_response_blocking(pending_llm_id, ANGEL_LLM_REQUEST_TIMEOUT_SECONDS)
                if actual_generated_code is None or actual_generated_code.startswith("<error"): 
                    reason = f"LLM code generation failed or timed out ({actual_generated_code or 'timeout'})"
                    self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "failure", "reason": reason})
                    self.current_processing_request = None; self.current_processing_stage = None
                else: 
                    logger.info("[AngelSystem] Code generated for agent %s. Proceeding to conceptual test.", agent_id)
                    self.current_processing_request = (agent_id, description, None, actual_generated_code, orig_ctx) 
                    self.current_processing_stage = "conceptual_test_request" 
            
            elif self.current_processing_stage == "conceptual_test_request" and gen_code:
                conceptual_test_prompt = self._build_conceptual_test_prompt(gen_code, description)
                concept_test_llm_id = llm.request(conceptual_test_prompt, self.world, model=llm.angel_generation_model)

                if concept_test_llm_id and not concept_test_llm_id.startswith("<error"):
                    self.current_processing_request = (agent_id, description, concept_test_llm_id, gen_code, orig_ctx)
                    self.current_processing_stage = "conceptual_test_response"
                else: 
                    reason = f"Failed to submit conceptual test to LLM ({concept_test_llm_id or 'request error'})"
                    self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "failure", "reason": reason})
                    self.current_processing_request = None; self.current_processing_stage = None

            elif self.current_processing_stage == "conceptual_test_response" and pending_llm_id and gen_code:
                conceptual_test_result_text = self._get_llm_response_blocking(pending_llm_id, ANGEL_LLM_REQUEST_TIMEOUT_SECONDS)
                test_passed = conceptual_test_result_text is not None and conceptual_test_result_text.strip().upper().startswith("PASS")

                if not test_passed:
                    reason = f"Conceptual test failed ({conceptual_test_result_text or 'timeout/error'})"
                    append_event_angel(self.world, agent_id, description, "conceptual_failure", {"reason": reason})
                    self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "failure", "reason": reason})
                else: 
                    logger.info("[AngelSystem] Conceptual test PASSED for agent %s. Granting ability.", agent_id)
                    path = angel_generator.generate_ability(description, stub_code=gen_code)
                    class_name = self._extract_class_name(path, description)
                    self._grant_to_agent(agent_id, class_name)
                    append_event_angel(self.world, agent_id, description, "granted", {"ability": class_name})
                    self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "success", "ability_class_name": class_name})
                
                self.current_processing_request = None; self.current_processing_stage = None
            elif self.current_processing_stage not in [None, "code_generation", "conceptual_test_request", "conceptual_test_response"]:
                 logger.error("[AngelSystem] Invalid processing state: %s. Resetting.", self.current_processing_stage)
                 self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "failure", "reason": f"Internal AngelSystem error: invalid state {self.current_processing_stage}"})
                 self.current_processing_request = None; self.current_processing_stage = None

        if not self.current_processing_request and self.request_queue:
            agent_id, description, _, _, orig_ctx = self.request_queue.pop(0) 
            self.current_processing_request = (agent_id, description, None, None, orig_ctx)
            logger.info("[AngelSystem] Processing NEW request for agent %s: '%s'", agent_id, description)

            vault_match = get_vault_index().lookup(description)
            if vault_match:
                append_event_angel(self.world, agent_id, description, "vault_hit", {"ability": vault_match})
                self._grant_to_agent(agent_id, vault_match)
                append_event_angel(self.world, agent_id, description, "granted", {"ability": vault_match})
                self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "success", "ability_class_name": vault_match})
                self.current_processing_request = None 
            else: 
                append_event_angel(self.world, agent_id, description, "llm_code_gen_attempt")
                prompt = self._build_angel_code_generation_prompt(description, templates.get_world_constraints_for_angel(), templates.get_code_scaffolds_for_angel())
                code_gen_llm_id = llm.request(prompt, self.world, model=llm.angel_generation_model)

                if code_gen_llm_id and not code_gen_llm_id.startswith("<error"):
                    self.current_processing_request = (agent_id, description, code_gen_llm_id, None, orig_ctx)
                    self.current_processing_stage = "code_generation"
                    logger.info("[AngelSystem] LLM Code Gen request sent (ID: %s) for agent %s, desc: '%s'", code_gen_llm_id, agent_id, description)
                else: 
                    reason = f"Failed to submit code generation to LLM ({code_gen_llm_id or 'request error'})"
                    self._finalize_request_processing(agent_id, description, orig_ctx, {"status": "failure", "reason": reason})
                    self.current_processing_request = None; self.current_processing_stage = None
        
        if not self.request_queue and not self.current_processing_request:
            if self.world.paused_for_angel: 
                logger.info("[AngelSystem] All ability requests processed. Unpausing world.")
            self.world.paused_for_angel = False

    def _grant_to_agent(self, agent_id: int, class_name: str) -> None:
        cm = getattr(self.world, "component_manager", None)
        if cm is None: return
        em = getattr(self.world, "entity_manager", None)
        if em is not None and not em.has_entity(agent_id):
            logger.warning("AngelSystem: attempted to grant ability to unknown agent_id %s", agent_id)
            return
        comp = cm.get_component(agent_id, KnownAbilitiesComponent)
        if comp is None: comp = KnownAbilitiesComponent(); cm.add_component(agent_id, comp)
        if class_name not in comp.known_class_names:
            comp.known_class_names.append(class_name)
            logger.info("[AngelSystem] Granted ability '%s' to agent %s.", class_name, agent_id)
        else:
            logger.info("[AngelSystem] Agent %s already knew ability '%s'.", class_name, agent_id)

    def _extract_class_name(self, path: Path, description_for_fallback: str) -> str:
        try:
            text = path.read_text(encoding="utf-8")
            m = re.search(r"class\s+(\w+)\s*\(Ability\)", text)
            if m: return m.group(1)
        except Exception as e:
            logger.error("[AngelSystem] Error extracting class name from %s: %s. Falling back.", path, e)
        slug = angel_generator._slugify(description_for_fallback)
        if "_" in path.stem and path.stem.rsplit("_",1)[1].isdigit(): 
            slug_from_filename = path.stem
            return angel_generator._class_name_from_slug(slug_from_filename)
        return angel_generator._class_name_from_slug(slug)

    def _build_angel_code_generation_prompt(self, desc: str, world_constraints: dict, code_scaffolds: dict) -> str:
        import json 
        parts = [
            "You are the Angel LLM responsible for generating new Ability code.",
            f"Requested ability description: {desc}",
            "The ability should be a complete Python class inheriting from 'Ability'.",
            "Include necessary imports like 'from typing import Any, Optional' and 'from agent_world.abilities.base import Ability'. Other game-specific imports like component types (e.g., 'from agent_world.core.components.position import Position') may also be needed.",
            "The 'execute' method should interact with 'world' object which has 'world.entity_manager', 'world.component_manager', 'world.spatial_index', etc. Use these to get entity data and components.",
            "Generated code must be functional. It will not be sandboxed beyond RestrictedPython's initial compile.",
            "Do not use placeholder comments like '# TODO: Implement logic'. Provide functional code.",
            "Return ONLY the valid Python code for the ability class file. No explanations before or after.",
            "", "World Constraints (available attributes on 'world' object, example components):", json.dumps(world_constraints, indent=2, default=str),
            "", "Code Scaffolds (use as a base for class structure):",
        ]
        for key, snippet in code_scaffolds.items(): parts.extend([f"# {key}", str(snippet)])
        parts.append("\nYour generated Python code for the Ability class (ONLY the code block, ensure it's a single Python code block):")
        return "\n".join(parts)

    def _build_conceptual_test_prompt(self, generated_code_str: str, original_request_str: str) -> str:
        clean_code = generated_code_str.strip()
        if clean_code.startswith("```python"): clean_code = clean_code[len("```python"):].strip()
        if clean_code.startswith("```"): clean_code = clean_code[len("```"):].strip()
        if clean_code.endswith("```"): clean_code = clean_code[:-len("```")].strip()
        
        return (
            "You are the Angel LLM performing a conceptual code review.\n"
            f"The original request was: '{original_request_str}'\n"
            "Here is the candidate Python code generated for this request:\n"
            "```python\n"
            f"{clean_code}\n"
            "```\n\n"
            "Review the Python code. Does it appear to functionally address the original request? "
            "Does it seem to use a typical game world API (e.g., world.component_manager.get_component(id, Type), world.entity_manager.has_entity(id)) correctly? "
            "Are there any obvious infinite loops, security risks for a Python exec environment (not a restricted sandbox), or major Python errors (syntax, undefined variables outside of typical game world context)? "
            "Respond with 'PASS' on a single line if it looks sound for a prototype, or 'FAIL' on a single line followed by a brief, concise reasoning on subsequent lines if there are critical issues."
        )

def get_angel_system(world: Any) -> AngelSystem:
    if not hasattr(world, "angel_system_instance") or world.angel_system_instance is None:
        world.angel_system_instance = AngelSystem(world)
    return world.angel_system_instance

def append_event_angel(world: Any, agent_id: int, description: str, stage: str, extra_data: dict | None = None) -> None:
    dest = getattr(world, "persistent_event_log_path", Path("persistent_events.log"))
    tick = getattr(getattr(world, "time_manager", None), "tick_counter", 0)
    data_to_log = {"stage": stage, "agent_id": agent_id, "description": description}
    if extra_data: data_to_log.update(extra_data)
    append_event(dest, tick, ANGEL_ACTION, data_to_log)

__all__ = ["AngelSystem", "get_angel_system"]