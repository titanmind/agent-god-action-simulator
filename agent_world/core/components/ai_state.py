# agent_world/core/components/ai_state.py
"""Component representing the AI-related state for an entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


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
    retries: int = 0

@dataclass(slots=True)
class AIState:
    """Simple container for an entity's personality, goals and plan."""

    personality: str
    goals: List[Goal] = field(default_factory=list)
    current_plan: List[ActionStep] = field(default_factory=list)
    
    pending_llm_prompt_id: str | None = None
    pending_llm_for_plan_step_action: str | None = None # Action string of plan step awaiting LLM

    # Task 5.2: New field to indicate agent is waiting for an ability
    waiting_for_ability_generation_desc: Optional[str] = None
    # Task 5.2: Field to store the name of a newly generated ability to hint its use
    newly_generated_ability_name: Optional[str] = None


    last_llm_action_tick: int = -1
    last_bt_direction_index: int = 0 
    last_action_failed_to_achieve_effect: bool = False 
    
    needs_immediate_rethink: bool = False 
    last_error: str | None = None 

    general_action_retries: int = 0 
    
    max_plan_step_retries: int = 3 
    last_plan_generation_tick: int = -1