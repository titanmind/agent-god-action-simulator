# agent_world/ai/llm/prompt_builder.py
"""Utilities for constructing deterministic LLM prompts."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, List, Set, Dict, Optional 

import threading
import asyncio
import logging

from ...core.world import World
from ...core.components.position import Position
from ...core.components.health import Health
from ...core.components.inventory import Inventory
from ...core.components.ai_state import AIState
from ...core.components.role import RoleComponent
from ...core.components.perception_cache import PerceptionCache
from ...systems.interaction.pickup import Tag
from ...systems.movement import pathfinding
from .llm_manager import LLMManager

logger = logging.getLogger(__name__)

_VISITED_OBJECTS_DURING_NORMALIZE: Set[int] = set()


def _get_memories(agent_id: int, k: int) -> List[str]:
    try: from ..memory import retrieve 
    except ImportError: return []
    try:
        memories = retrieve(agent_id, k)
        if isinstance(memories, list): return [str(m) for m in memories]
    except Exception: pass # pylint: disable=broad-except
    return []


def _normalize(obj: Any) -> Any:
    global _VISITED_OBJECTS_DURING_NORMALIZE
    if obj is None or isinstance(obj, (str, int, float, bool)): return obj
    if isinstance(obj, type): return f"<Class {obj.__module__}.{obj.__name__}>"
    obj_id = id(obj)
    if obj_id in _VISITED_OBJECTS_DURING_NORMALIZE: return f"<CircularRef id:{obj_id} type:{type(obj).__name__}>"
    _VISITED_OBJECTS_DURING_NORMALIZE.add(obj_id)
    try:
        if is_dataclass(obj) and not isinstance(obj, type):
            try: data = asdict(obj); return {k: _normalize(v) for k, v in data.items()}
            except TypeError: # pragma: no cover
                if hasattr(obj, "__dict__"): return {str(k): _normalize(v) for k, v in vars(obj).items() if not str(k).startswith("_")}
                return f"<UnserializableDataclass id:{obj_id} type:{type(obj).__name__}>"
        elif isinstance(obj, dict): return {str(k): _normalize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)): return [_normalize(v) for v in list(obj)]
        elif isinstance(obj, World): return {"type": "WorldSummary", "size": obj.size, "current_tick": obj.time_manager.tick_counter if obj.time_manager else -1}
        elif hasattr(obj, "__dict__"): 
            items_to_normalize = {}
            for k, v in vars(obj).items():
                k_str = str(k)
                if k_str.startswith("_"): continue
                if isinstance(v, (threading.Thread, asyncio.Future, asyncio.AbstractEventLoop, LLMManager)): items_to_normalize[k_str] = f"<SkippedInstance type:{type(v).__name__}>"; continue
                items_to_normalize[k_str] = _normalize(v)
            return items_to_normalize
        return f"<UnserializableObject type:{type(obj).__name__} id:{obj_id}>"
    finally:
        if obj_id in _VISITED_OBJECTS_DURING_NORMALIZE: _VISITED_OBJECTS_DURING_NORMALIZE.remove(obj_id)


def build_prompt(agent_id: int, world: World, *, memory_k: int = 5) -> str: 
    global _VISITED_OBJECTS_DURING_NORMALIZE 
    _VISITED_OBJECTS_DURING_NORMALIZE = set() 

    em = world.entity_manager; cm = world.component_manager; tm = world.time_manager
    if not all([em, cm, tm]): return "Error: World managers not fully initialized. Cannot build prompt."

    world_width, world_height = world.size
    agent_pos: Optional[Position] = cm.get_component(agent_id, Position)
    agent_ai_state: Optional[AIState] = cm.get_component(agent_id, AIState)
    agent_inventory: Optional[Inventory] = cm.get_component(agent_id, Inventory)
    perception_cache = cm.get_component(agent_id, PerceptionCache)

    if agent_id == 2 and tm:
        logger.debug("DEBUG AGENT 2 in build_prompt (Tick %s)", tm.tick_counter)
        if agent_ai_state:
            logger.debug("Agent 2 AIState object ID: %s, Goals RAW: %s", id(agent_ai_state), agent_ai_state.goals)
        else:
            logger.debug("Agent 2 AIState is None in build_prompt")

    current_pos_str = f"({agent_pos.x}, {agent_pos.y})" if agent_pos else "Unknown"
    
    my_goals_list = agent_ai_state.goals if agent_ai_state else []

    def _goal_to_str(goal: Any) -> str:
        if hasattr(goal, "type"):
            parts = [str(goal.type)]
            if getattr(goal, "target", None) is not None:
                parts.append(str(goal.target))
            if getattr(goal, "conditions", {}):
                cond = ", ".join(f"{k}={v}" for k, v in goal.conditions.items())
                parts.append(f"[{cond}]")
            return " ".join(parts)
        return str(goal)

    goal_strings = [_goal_to_str(g) for g in my_goals_list]
    my_goals_str = ", ".join(goal_strings) if goal_strings else "None"

    my_known_abilities_str = "None"
    ability_system_instance = getattr(world, 'ability_system_instance', None)
    if ability_system_instance and ability_system_instance.abilities:
        known_ability_names = sorted([name for name in ability_system_instance.abilities.keys()])
        if known_ability_names: my_known_abilities_str = ", ".join(known_ability_names)

    role_comp = cm.get_component(agent_id, RoleComponent)
    can_request_abilities = role_comp.can_request_abilities if role_comp else True

    agent_specific_world_data = {} 
    agent_specific_world_data["world_info"] = {
        "size": f"{world_width}x{world_height} (X:0-{world_width-1}, Y:0-{world_height-1})",
        "current_tick": tm.tick_counter if tm else -1, 
        "your_current_position": current_pos_str,
    }

    agent_components_dict: Dict[str, Any] = {}
    if em.has_entity(agent_id):
        raw_components = cm._components.get(agent_id, {})
        for comp_name_type, comp_instance in raw_components.items():
            comp_name = comp_name_type.__name__ if isinstance(comp_name_type, type) else str(comp_name_type)
            _VISITED_OBJECTS_DURING_NORMALIZE = set()
            if not isinstance(comp_instance, PerceptionCache): agent_components_dict[comp_name] = _normalize(comp_instance)
    agent_specific_world_data["my_components"] = agent_components_dict
    
    visible_entities_and_items_info_standard = [] 
    if perception_cache and perception_cache.visible: 
        for visible_eid in perception_cache.visible:
            if not em.has_entity(visible_eid): continue
            entity_info: Dict[str, Any] = {"id": visible_eid}
            v_pos = cm.get_component(visible_eid, Position); v_health = cm.get_component(visible_eid, Health)
            v_aistate_comp = cm.get_component(visible_eid, AIState); v_tag = cm.get_component(visible_eid, Tag)
            if v_pos: entity_info["position"] = f"({v_pos.x}, {v_pos.y})"
            if v_health: entity_info["health"] = f"{v_health.cur}/{v_health.max}"
            if v_aistate_comp: entity_info["type"] = "npc"
            if v_tag: entity_info["type"] = "item"; entity_info["tag_name"] = v_tag.name 
            if "type" not in entity_info: entity_info["type"] = "unknown_entity"
            visible_entities_and_items_info_standard.append(entity_info)
    if visible_entities_and_items_info_standard: agent_specific_world_data["visible_entities_and_items"] = sorted(visible_entities_and_items_info_standard, key=lambda x:x.get("id",0))
    else: agent_specific_world_data["visible_entities_and_items"] = "You see no other entities or items."

    _VISITED_OBJECTS_DURING_NORMALIZE = set()
    normalized_view = _normalize(agent_specific_world_data)
    try: serialized_view = json.dumps(normalized_view, sort_keys=True, indent=2, default=str)
    except TypeError as e: serialized_view = f'{{"error": "Failed to serialize agent world view", "details": "{str(e)}"}}'

    memories = _get_memories(agent_id, memory_k)
    mem_section = ""; 
    if memories: 
        try: mem_json = json.dumps(memories, sort_keys=True, indent=2)
        except TypeError: mem_json = "<error serializing memories>"
        mem_section = f"\n\nRecent Memories:\n{mem_json}"

    my_personality = agent_ai_state.personality if agent_ai_state else "default"
    # FIX: Use the renamed attribute 'last_action_failed_to_achieve_effect'
    last_action_failed_status = agent_ai_state.last_action_failed_to_achieve_effect if agent_ai_state else False
    
    dynamic_advice_lines = []
    # FIX: Use the renamed attribute
    if last_action_failed_status and my_goals_list and can_request_abilities:
        dynamic_advice_lines.append("Your last action did not achieve its intended effect (e.g. movement blocked). If an obstacle hinders your goals, consider `GENERATE_ABILITY`.")
    if my_known_abilities_str != "None":
        dynamic_advice_lines.append("Review your 'known abilities'. Can any help achieve goals or overcome obstacles?")
    
    has_any_visible_item = any(e_info.get("type") == "item" for e_info in visible_entities_and_items_info_standard)
    inventory_has_space_for_general_pickup = len(agent_inventory.items) < agent_inventory.capacity if agent_inventory else False
    if has_any_visible_item and inventory_has_space_for_general_pickup:
        dynamic_advice_lines.append("You see items nearby. If useful and you have space, consider `PICKUP <item_id>`." )

    obstacle_note = ""
    if agent_ai_state and my_goals_list and agent_pos:
        executing_obstacle_step = False
        if agent_ai_state.current_plan:
            first_step = agent_ai_state.current_plan[0]
            # Check if the current LLM request is for this specific obstacle step
            step_action_key_for_pending_llm = f"{first_step.action}_{id(first_step)}"
            if (agent_ai_state.pending_llm_prompt_id is not None and
                agent_ai_state.pending_llm_for_plan_step_action == step_action_key_for_pending_llm and
                (first_step.step_type == "deal_with_obstacle" or 
                 (first_step.action and first_step.action.upper() == "DEAL_WITH_OBSTACLE"))):
                executing_obstacle_step = True
        
        if not executing_obstacle_step: # Only add general obstacle note if not actively dealing with one via LLM
            goal = my_goals_list[0]
            target = getattr(goal, "target", None)
            target_coords = None
            if isinstance(target, int):
                t_pos = cm.get_component(target, Position)
                if t_pos:
                    target_coords = (t_pos.x, t_pos.y)
            elif isinstance(target, (tuple, list)) and len(target) == 2:
                target_coords = (int(target[0]), int(target[1]))
            if target_coords:
                dx = target_coords[0] - agent_pos.x
                dy = target_coords[1] - agent_pos.y
                # Check immediate step towards target
                next_step_x, next_step_y = agent_pos.x, agent_pos.y
                if abs(dx) > abs(dy): next_step_x += (1 if dx > 0 else -1)
                elif dy != 0: next_step_y += (1 if dy > 0 else -1)
                
                if (next_step_x, next_step_y) != (agent_pos.x, agent_pos.y) and \
                   pathfinding.is_blocked((next_step_x, next_step_y)):
                    obstacle_at = (next_step_x, next_step_y)
                    target_display = target if isinstance(target, int) else target_coords
                    obstacle_note = (
                        f"SYSTEM NOTE: Your direct path to current goal target {target_display} "
                        f"is blocked by an obstacle at {obstacle_at}. Consider alternative actions or abilities."
                    )

    dynamic_advice_section = ""
    if dynamic_advice_lines:
        advice_text = "\n".join([f"- {line}" for line in dynamic_advice_lines])
        dynamic_advice_section = f"Considerations for This Turn:\n{advice_text}"
    
    base_lines = [
        f"You are Agent {agent_id}. Your personality is \"{my_personality}\".",
        f"Your current position is {current_pos_str}. The world is a grid of size {world_width}x{world_height}.",
        "",
        "Your primary directive is to achieve your goals. Use exploration and interaction intelligently.",
        "If you are at a world boundary, DO NOT try to move further in that direction.",
    ]
    if can_request_abilities:
        base_lines.append('If you need a new skill for your goals or to overcome an obstacle, use "GENERATE_ABILITY <description>".')
    base_lines.append('After an ability is generated (it will appear in \"Abilities You Know\" next turn), you can use "USE_ABILITY <AbilityClassName> [target_id]".')
    base_lines.append('Formulate a plan or a single action. If you plan multiple steps, use LOG for the plan then take the first step.')
    base_instructions = "\n".join(base_lines)

    action_lines = [
        "Available Actions (Strictly respond with ONLY ONE action string, OR a LOG action followed by another action on a new line):",
        '- "LOG <message>" (e.g., "LOG I see item 7 at (10,12).")',
        '- "MOVE <N|S|E|W>" (e.g., "MOVE N")',
        '- "ATTACK <target_id>" (e.g., "ATTACK 15")',
        '- "IDLE"',
    ]
    if can_request_abilities:
        action_lines.append('- "GENERATE_ABILITY <description>" (e.g., "GENERATE_ABILITY create healing potion")')
    action_lines.extend([
        '- "USE_ABILITY <AbilityClassName> [target_id]" (e.g., "USE_ABILITY MeleeStrike 15" or "USE_ABILITY SampleFireball 15")',
        '- "PICKUP <item_id>" (e.g., "PICKUP 4")',
    ])
    action_list_text = "\n".join(action_lines)

    focus_lines = ["--- FOCUS FOR THIS TURN ---", f"YOUR CURRENT GOALS: {my_goals_str}"]
    if can_request_abilities: # Only show known abilities if they *can* request/use them
        focus_lines.append(f"ABILITIES YOU KNOW: {my_known_abilities_str}")
    if dynamic_advice_section:
        focus_lines.append(dynamic_advice_section)
    focus_lines.append("--- END FOCUS ---")
    focus_section = "\n".join(focus_lines)

    prompt_parts = []
    if agent_ai_state and agent_ai_state.last_error: # Prepend system note about previous error
        prompt_parts.append(f"SYSTEM NOTE (from previous turn): {agent_ai_state.last_error}")
    
    if obstacle_note:
        prompt_parts.append(obstacle_note)

    prompt_parts.extend([
        base_instructions,
        f"--- Current World State for Agent {agent_id} (Tick: {tm.tick_counter if tm else 'N/A'}) ---",
        serialized_view,
        mem_section,
        "", # Blank line for separation
        focus_section,
        action_list_text,
        "Based on your GOALS and current situation, what is Your Action:"
    ])
    prompt = "\n".join(filter(None, prompt_parts)) # Join non-empty parts

    current_tick_for_log = tm.tick_counter if tm else "N/A"
    logger.debug(
        "\n--- [PromptBuilder Agent %s Tick %s] FULL STANDARD PROMPT SENT ---\n%s\n--- END FULL STANDARD PROMPT ---\n",
        agent_id,
        current_tick_for_log,
        prompt,
    )
        
    return prompt

__all__ = ["build_prompt", "_normalize", "_get_memories"]