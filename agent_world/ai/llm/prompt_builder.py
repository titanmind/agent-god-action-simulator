
# agent-god-action-simulator/agent_world/ai/llm/prompt_builder.py
"""Utilities for constructing deterministic LLM prompts."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, List, Set, Dict, Optional 

import threading
import asyncio

from ...core.world import World
from ...core.components.position import Position
from ...core.components.health import Health 
from ...core.components.inventory import Inventory 
from ...core.components.ai_state import AIState
from ...core.components.perception_cache import PerceptionCache
from ...systems.interaction.pickup import Tag 
from ...systems.ai.actions import PLAYER_ID 
from .llm_manager import LLMManager
from ...systems.ability.ability_system import AbilitySystem
from ...systems.movement.pathfinding import is_blocked 

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
    global _VISITED_OBJECTS_DURING_NORMALIZE # Ensure global is used
    _VISITED_OBJECTS_DURING_NORMALIZE = set() 

    em = world.entity_manager; cm = world.component_manager; tm = world.time_manager
    if not all([em, cm, tm]): return "Error: World managers not fully initialized. Cannot build prompt."

    world_width, world_height = world.size
    agent_pos: Optional[Position] = cm.get_component(agent_id, Position)
    agent_ai_state: Optional[AIState] = cm.get_component(agent_id, AIState)
    agent_inventory: Optional[Inventory] = cm.get_component(agent_id, Inventory)

    # +++ DEBUG BLOCK for Agent 2 Goals +++
    if agent_id == 2 and tm: # Check tm exists for tick_counter
        print(f"[[[[[[[[[[ DEBUG AGENT 2 in build_prompt (Tick {tm.tick_counter}) ]]]]]]]]]]")
        if agent_ai_state:
            print(f"[[[[[ Agent 2 AIState object ID: {id(agent_ai_state)}, Goals RAW: {agent_ai_state.goals} ]]]]]")
        else:
            print(f"[[[[[ Agent 2 AIState is None in build_prompt ]]]]]")
    # +++ END DEBUG BLOCK +++

    current_pos_str = f"({agent_pos.x}, {agent_pos.y})" if agent_pos else "Unknown"
    
    my_goals_list = agent_ai_state.goals if agent_ai_state else []
    my_goals_str = ", ".join(my_goals_list) if my_goals_list else "None specified"
    # print(f"[PromptBuilder DEBUG] For Agent {agent_id} at Tick {tm.tick_counter if tm else 'N/A'}, goals are: {my_goals_list}, resulting in my_goals_str: '{my_goals_str}'")

    my_known_abilities_str = "None"
    ability_system_instance = getattr(world, 'ability_system_instance', None)
    if ability_system_instance and ability_system_instance.abilities:
        known_ability_names = sorted([name for name in ability_system_instance.abilities.keys()])
        if known_ability_names: my_known_abilities_str = ", ".join(known_ability_names)

    # --- Determine Critical Advice ---
    critical_advice_text = ""
    primary_goal_item_id: Optional[int] = None
    if my_goals_list:
        for goal_str in my_goals_list:
            if "acquire item" in goal_str.lower():
                try: primary_goal_item_id = int(goal_str.lower().split("acquire item")[-1].strip())
                except ValueError: pass
                break
    
    is_goal_item_visible = False
    visible_goal_item_details: Optional[Dict[str, Any]] = None
    perception_cache = cm.get_component(agent_id, PerceptionCache)
    if perception_cache and perception_cache.visible:
        for visible_eid in perception_cache.visible: 
            if em.has_entity(visible_eid) and visible_eid == primary_goal_item_id:
                v_pos_comp = cm.get_component(visible_eid, Position)
                v_tag_comp = cm.get_component(visible_eid, Tag)
                if v_pos_comp and v_tag_comp and v_tag_comp.name == "item":
                    is_goal_item_visible = True
                    visible_goal_item_details = {
                        "id": visible_eid, "position": f"({v_pos_comp.x},{v_pos_comp.y})",
                        "type": "item", "tag_name": v_tag_comp.name
                    }
                    break 
    
    known_obstacle_removal_ability_name: Optional[str] = None
    if my_known_abilities_str != "None":
        # Simplistic check for any ability containing "DisintegrateObstacle" or "RemoveObstacle"
        # This should be made more robust, e.g. by ability tags or specific naming conventions.
        disintegrate_abilities = [name for name in my_known_abilities_str.split(", ") if "DisintegrateObstacle" in name or "RemoveObstacle" in name]
        if disintegrate_abilities:
            known_obstacle_removal_ability_name = sorted(disintegrate_abilities)[-1] # crude way to get newest if multiple from _1, _2 etc.

    if agent_pos and primary_goal_item_id and is_goal_item_visible and visible_goal_item_details:
        goal_item_pos_str = visible_goal_item_details['position']
        goal_item_x = int(goal_item_pos_str.strip('()').split(',')[0]); goal_item_y = int(goal_item_pos_str.strip('()').split(',')[1])
        
        path_to_goal_blocked = False
        obs_pos_tuple: Optional[tuple[int,int]] = None
        blocked_direction = ""

        if agent_pos.x == goal_item_x: 
            if agent_pos.y > goal_item_y and is_blocked((agent_pos.x, agent_pos.y - 1)): path_to_goal_blocked = True; obs_pos_tuple = (agent_pos.x, agent_pos.y -1); blocked_direction="North"
            elif agent_pos.y < goal_item_y and is_blocked((agent_pos.x, agent_pos.y + 1)): path_to_goal_blocked = True; obs_pos_tuple = (agent_pos.x, agent_pos.y +1); blocked_direction="South"
        elif agent_pos.y == goal_item_y: 
            if agent_pos.x > goal_item_x and is_blocked((agent_pos.x - 1, agent_pos.y)): path_to_goal_blocked = True; obs_pos_tuple = (agent_pos.x -1, agent_pos.y); blocked_direction="West"
            elif agent_pos.x < goal_item_x and is_blocked((agent_pos.x + 1, agent_pos.y)): path_to_goal_blocked = True; obs_pos_tuple = (agent_pos.x +1, agent_pos.y); blocked_direction="East"
        
        if path_to_goal_blocked and obs_pos_tuple:
            if known_obstacle_removal_ability_name:
                critical_advice_text = (
                    f"CRITICAL OBSTACLE: An obstacle at {obs_pos_tuple} is DIRECTLY blocking your path {blocked_direction} "
                    f"to your goal item {primary_goal_item_id} at ({goal_item_x},{goal_item_y}). "
                    f"You know the ability '{known_obstacle_removal_ability_name}'. You MUST use "
                    f"`USE_ABILITY {known_obstacle_removal_ability_name}` to remove it."
                )
            else:
                critical_advice_text = (
                    f"CRITICAL OBSTACLE: An obstacle at {obs_pos_tuple} is DIRECTLY blocking your path {blocked_direction} "
                    f"to your goal item {primary_goal_item_id} at ({goal_item_x},{goal_item_y}). "
                    "You MUST use `GENERATE_ABILITY <description>` to overcome this (e.g., "
                    "'GENERATE_ABILITY remove obstacle' or 'GENERATE_ABILITY phase through wall')."
                )
        
        if not path_to_goal_blocked: 
            inventory_has_space = len(agent_inventory.items) < agent_inventory.capacity if agent_inventory else False
            can_reach_item = (agent_pos.x == goal_item_x and agent_pos.y == goal_item_y) or \
                             (abs(agent_pos.x - goal_item_x) + abs(agent_pos.y - goal_item_y) == 1 and not is_blocked((goal_item_x,goal_item_y)))
            if can_reach_item:
                if inventory_has_space:
                    pickup_advice = (
                        f"CRITICAL GOAL REACHABLE: Your goal item {primary_goal_item_id} is at {goal_item_pos_str} and you are "
                        f"next to it or on it! You MUST use `PICKUP {primary_goal_item_id}` NOW."
                    )
                else: pickup_advice = f"Your goal item {primary_goal_item_id} is at {goal_item_pos_str}, but inventory is full. Cannot `PICKUP`."
                if not critical_advice_text: critical_advice_text = pickup_advice
    
    if critical_advice_text:
        critical_action_list = ["- LOG <your reasoning IF you cannot follow the MUST instruction below>"]
        if "USE_ABILITY" in critical_advice_text and known_obstacle_removal_ability_name:
            critical_action_list.insert(0, f"- USE_ABILITY {known_obstacle_removal_ability_name}")
        elif "GENERATE_ABILITY" in critical_advice_text:
             critical_action_list.insert(0, "- GENERATE_ABILITY <description>")
        if "PICKUP" in critical_advice_text and primary_goal_item_id is not None: 
            critical_action_list.insert(0, f"- PICKUP {primary_goal_item_id}")
        
        critical_actions_str = "\n".join(critical_action_list)
        prompt = f"""You are Agent {agent_id}.
Your Position: {current_pos_str}.
YOUR GOAL: {my_goals_str}.
ABILITIES YOU KNOW: {my_known_abilities_str}

CRITICAL SITUATION:
{critical_advice_text} 

You MUST choose an action to address this critical situation from the list below.
If you choose LOG, explain why you cannot follow the MUST instruction.

Available actions for THIS CRITICAL SITUATION:
{critical_actions_str}

Your Action to address the CRITICAL SITUATION:"""
        current_tick_for_log = tm.tick_counter if tm else "N/A"
        print(f"\n--- [PromptBuilder Agent {agent_id} Tick {current_tick_for_log}] FULL CRITICAL PROMPT SENT ---")
        print(prompt)
        print("--- END FULL CRITICAL PROMPT ---\n")
        return prompt

    # --- If not a critical situation, build the standard prompt ---
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
    last_bt_move_failed_status = agent_ai_state.last_bt_move_failed if agent_ai_state else False
    
    dynamic_advice_lines = [] 
    if last_bt_move_failed_status and my_goals_list: 
        dynamic_advice_lines.append("Your last automatic movement was blocked. If an obstacle hinders your goals, consider `GENERATE_ABILITY`.")
    if my_known_abilities_str != "None":
        dynamic_advice_lines.append("Review your 'known abilities'. Can any help achieve goals or overcome obstacles?")
    
    has_any_visible_item = any(e_info.get("type") == "item" for e_info in visible_entities_and_items_info_standard) # Use standard list
    inventory_has_space_for_general_pickup = len(agent_inventory.items) < agent_inventory.capacity if agent_inventory else False
    if has_any_visible_item and not is_goal_item_visible and inventory_has_space_for_general_pickup :
         dynamic_advice_lines.append("You see other items. If useful and you have space, consider `PICKUP <item_id>`.")

    dynamic_advice_section = ""
    if dynamic_advice_lines:
        advice_text = "\n".join([f"- {line}" for line in dynamic_advice_lines])
        dynamic_advice_section = f"Considerations for This Turn:\n{advice_text}"
    
    base_instructions = f"""You are Agent {agent_id}. Your personality is "{my_personality}".
Your current position is {current_pos_str}. The world is a grid of size {world_width}x{world_height}.
Player (ID {PLAYER_ID}) is controlled by a human.

Your primary directive is to achieve your goals. Use exploration and interaction intelligently.
If you are at a world boundary, DO NOT try to move further in that direction.
If you need a new skill for your goals or to overcome an obstacle, use "GENERATE_ABILITY <description>".
After an ability is generated (it will appear in 'Abilities You Know' next turn), you can use "USE_ABILITY <AbilityClassName>".
Formulate a plan or a single action. If you plan multiple steps, use LOG for the plan then take the first step.
"""
    action_list_text = """
Available Actions (Strictly respond with ONLY ONE action string, OR a LOG action followed by another action on a new line):
- "LOG <message>" (e.g., "LOG I see item 7 at (10,12).")
- "MOVE <N|S|E|W>" (e.g., "MOVE N")
- "ATTACK <target_id>" (e.g., "ATTACK 15")
- "IDLE"
- "GENERATE_ABILITY <description>" (e.g., "GENERATE_ABILITY create healing potion")
- "USE_ABILITY <AbilityClassName> [target_id]" (e.g., "USE_ABILITY MeleeStrike 15")
- "PICKUP <item_id>" (e.g., "PICKUP 4")
"""
    prompt = f"""{base_instructions}
--- Current World State for Agent {agent_id} (Tick: {tm.tick_counter if tm else 'N/A'}) ---
{serialized_view}
{mem_section}

--- FOCUS FOR THIS TURN ---
YOUR CURRENT GOALS: {my_goals_str}
ABILITIES YOU KNOW: {my_known_abilities_str}
{dynamic_advice_section} 
--- END FOCUS ---
{action_list_text}
Based on your GOALS and current situation, what is Your Action:"""
    
    current_tick_for_log = tm.tick_counter if tm else "N/A"
    print(f"\n--- [PromptBuilder Agent {agent_id} Tick {current_tick_for_log}] FULL STANDARD PROMPT SENT ---")
    print(prompt)
    print("--- END FULL STANDARD PROMPT ---\n")
        
    return prompt

__all__ = ["build_prompt", "_normalize", "_get_memories"]