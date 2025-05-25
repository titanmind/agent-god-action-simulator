
# agent_world/core/components/ai_state.py
"""Component representing the AI-related state for an entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass(slots=True)
class Goal:
    """Representation of a high level goal for an agent."""

    type: str
    target: int | None = None
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionStep:
    """Single planned step an agent should take."""

    action: str
    target: int | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    step_type: str | None = None
    retries: int = 0  # Task 3.1: Per-step retry counter

@dataclass(slots=True)
class AIState:
    """Simple container for an entity's personality, goals and plan."""

    personality: str
    goals: List[Goal] = field(default_factory=list)
    current_plan: List[ActionStep] = field(default_factory=list)
    pending_llm_prompt_id: str | None = None
    # Stores the action string of the plan step for which the current pending_llm_prompt_id was issued.
    # This helps associate LLM responses back to the correct plan step when an agent has a multi-step plan
    # and some steps require LLM deliberation.
    pending_llm_for_plan_step_action: str | None = None

    last_llm_action_tick: int = -1
    last_bt_direction_index: int = 0 
    # Task 3.2: Renamed flag. True if the last action taken by this agent
    # (whether from plan, LLM, or BT) failed to achieve its intended effect 
    # (e.g., a move was blocked, an ability use failed).
    last_action_failed_to_achieve_effect: bool = False 
    
    needs_immediate_rethink: bool = False # For Angel system or other immediate triggers
    last_error: str | None = None # General error string, e.g., from Angel system failure

    # This can be used as a global retry for the *entire plan* if needed,
    # or for general LLM decision failures not tied to a specific plan step.
    # Per-step retries are now on ActionStep.retries.
    # For now, let's consider this for general LLM decision retries if not tied to a plan step.
    general_action_retries: int = 0 
    
    max_plan_step_retries: int = 3 # Max retries for a single step before abandoning that step/plan
    last_plan_generation_tick: int = -1