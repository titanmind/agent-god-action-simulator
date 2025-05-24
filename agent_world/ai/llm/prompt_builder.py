
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
from ...core.components.ai_state import AIState
from ...core.components.perception_cache import PerceptionCache
from ...systems.interaction.pickup import Tag 
from ...systems.interaction.trading import get_local_prices
from ...systems.ai.actions import PLAYER_ID
from .llm_manager import LLMManager

_VISITED_OBJECTS_DURING_NORMALIZE: Set[int] = set()


def _get_memories(agent_id: int, k: int) -> List[str]:
    try:
        from ..memory import retrieve
    except ImportError:
        return []
    try:
        memories = retrieve(agent_id, k)
        if isinstance(memories, list):
            return [str(m) for m in memories]
    except Exception:
        pass
    return []


def _normalize(obj: Any) -> Any:
    global _VISITED_OBJECTS_DURING_NORMALIZE
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, type):
        return f"<Class {obj.__module__}.{obj.__name__}>"
    obj_id = id(obj)
    if obj_id in _VISITED_OBJECTS_DURING_NORMALIZE:
        return f"<CircularRef id:{obj_id} type:{type(obj).__name__}>"
    _VISITED_OBJECTS_DURING_NORMALIZE.add(obj_id)
    try:
        if is_dataclass(obj) and not isinstance(obj, type):
            try:
                data = asdict(obj)
                return {k: _normalize(v) for k, v in data.items()}
            except TypeError:
                if hasattr(obj, "__dict__"):
                    return {
                        str(k): _normalize(v)
                        for k, v in vars(obj).items()
                        if not str(k).startswith("_")
                    }
                return f"<UnserializableDataclass id:{obj_id} type:{type(obj).__name__}>"
        elif isinstance(obj, dict):
            return {str(k): _normalize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [_normalize(v) for v in list(obj)]
        elif isinstance(obj, World): 
            return {
                "type": "WorldSummary",
                "size": obj.size,
                "current_tick": obj.time_manager.tick_counter if obj.time_manager else -1,
            }
        elif hasattr(obj, "__dict__"):
            items_to_normalize = {}
            for k, v in vars(obj).items():
                k_str = str(k)
                if k_str.startswith("_"): continue
                if isinstance(v, (
                    threading.Thread, asyncio.Future, asyncio.AbstractEventLoop, LLMManager,
                )):
                    items_to_normalize[k_str] = f"<SkippedInstance type:{type(v).__name__}>"
                    continue
                items_to_normalize[k_str] = _normalize(v)
            return items_to_normalize
        return f"<UnserializableObject type:{type(obj).__name__} id:{obj_id}>"
    finally:
        if obj_id in _VISITED_OBJECTS_DURING_NORMALIZE:
            _VISITED_OBJECTS_DURING_NORMALIZE.remove(obj_id)


def build_prompt(agent_id: int, world: World, *, memory_k: int = 5) -> str: 
    global _VISITED_OBJECTS_DURING_NORMALIZE
    _VISITED_OBJECTS_DURING_NORMALIZE = set()

    agent_specific_world_data: Dict[str, Any] = {}

    em = world.entity_manager
    cm = world.component_manager
    tm = world.time_manager

    world_width, world_height = world.size
    agent_pos: Optional[Position] = cm.get_component(agent_id, Position) if cm else None

    current_pos_str = f"({agent_pos.x}, {agent_pos.y})" if agent_pos else "Unknown"
    agent_specific_world_data["world_info"] = {
        "size": f"{world_width}x{world_height} (Width x Height, X from 0 to {world_width-1}, Y from 0 to {world_height-1})",
        "current_tick": tm.tick_counter if tm else -1,
        "your_current_position": current_pos_str,
    }
    
    agent_components_dict: Dict[str, Any] = {}
    if em and cm and em.has_entity(agent_id):
        raw_components = cm._components.get(agent_id, {}) if hasattr(cm, '_components') else {}
        for comp_name_type, comp_instance in raw_components.items():
            comp_name = comp_name_type.__name__ if isinstance(comp_name_type, type) else str(comp_name_type)
            _VISITED_OBJECTS_DURING_NORMALIZE = set()
            if not isinstance(comp_instance, PerceptionCache):
                 agent_components_dict[comp_name] = _normalize(comp_instance)
    agent_specific_world_data["my_components"] = agent_components_dict

    visible_entities_info = []
    if cm:
        perception_cache = cm.get_component(agent_id, PerceptionCache)
        if perception_cache and perception_cache.visible:
            for visible_eid in perception_cache.visible:
                if not em or not em.has_entity(visible_eid): continue

                entity_info: Dict[str, Any] = {"id": visible_eid}
                v_pos = cm.get_component(visible_eid, Position)
                if v_pos: entity_info["position"] = f"({v_pos.x}, {v_pos.y})"
                
                v_health = cm.get_component(visible_eid, Health)
                if v_health: entity_info["health"] = f"{v_health.cur}/{v_health.max}"
                                
                v_aistate = cm.get_component(visible_eid, AIState)
                if v_aistate: 
                    entity_info["type"] = "npc"
                
                v_tag = cm.get_component(visible_eid, Tag)
                if v_tag: 
                    entity_info["type"] = "item"
                    entity_info["tag"] = v_tag.name

                if "type" not in entity_info: entity_info["type"] = "unknown"
                visible_entities_info.append(entity_info)
    
    if visible_entities_info:
        agent_specific_world_data["visible_entities"] = visible_entities_info
    else:
        agent_specific_world_data["visible_entities"] = "You see no other entities or items."

    _VISITED_OBJECTS_DURING_NORMALIZE = set()
    normalized_view = _normalize(agent_specific_world_data)
    
    try:
        serialized_view = json.dumps(normalized_view, sort_keys=True, indent=2, default=str)
    except TypeError as e:
        serialized_view = f'{{"error": "Failed to serialize agent world view", "details": "{str(e)}"}}'

    price_section = "" 
    # ... price logic ...

    memories = _get_memories(agent_id, memory_k)
    mem_section = ""
    if memories:
        try:
            mem_json = json.dumps(memories, sort_keys=True, indent=2)
            mem_section = f"\n\nRecent Memories:\n{mem_json}"
        except TypeError:
            mem_section = "\n\nRecent Memories: <error serializing memories>"

    my_ai_state = agent_specific_world_data.get("my_components", {}).get("AIState", {})
    my_personality = my_ai_state.get("personality", "default")
    my_goals = my_ai_state.get("goals", "None specified") # If goals is an empty list, it will show as []
    if not my_goals: my_goals = "None specified" # Make it more readable if list is empty

    player_info_string = f"Player (ID {PLAYER_ID}) is controlled by a human and is a potential interaction target." if PLAYER_ID != agent_id else "You are the player."

    # --- Enhanced Prompt Instructions ---
    instructions = f"""You are Agent {agent_id}. Your personality is "{my_personality}".
Your current position is {current_pos_str}. The world is a grid of size {world_width}x{world_height} (X from 0 to {world_width-1}, Y from 0 to {world_height-1}).
IMPORTANT: Do NOT attempt to MOVE outside these boundaries. If at a boundary, choose a different direction or action.
{player_info_string}

Your primary directive is to explore actively and interact intelligently.
Your current specific goals: {my_goals}

Available Actions (Strictly respond with ONLY ONE action string from this list, followed by arguments if any):
- "MOVE <N|S|E|W>": Move one step. Example: "MOVE N"
- "ATTACK <target_id>": Attack a visible NPC or entity with the given ID. Example: "ATTACK 15"
- "LOG <message>": Record a message, observation, or plan. Example: "LOG Found an ore deposit at my location. Will try to mine it later."
- "IDLE": Do nothing this turn. (Use sparingly, prefer active exploration or observation).
- "GENERATE_ABILITY <description>": Request a new ability if you are stuck or need a new capability. Be specific. Example: "GENERATE_ABILITY create a map of explored areas"
- "USE_ABILITY <ability_name> [target_id]": Use an existing ability you possess. Example: "USE_ABILITY MeleeStrike 15" (Target is optional for some abilities)
- "PICKUP <item_id>": Attempt to pick up a visible item if it's useful. Example: "PICKUP 4" (Note: This action's success depends on game rules.)

Decision Process:
1. Observe your `my_components` and `visible_entities`.
2. Consider your `personality` and `goals`.
3. If you are at a world boundary (e.g., X=0, X={world_width-1}, Y=0, Y={world_height-1}), DO NOT try to move further in that direction. Choose another valid move or action.
4. Formulate a plan or a single action. If you plan multiple steps, use LOG for the plan then take the first step.
5. If you see something interesting (item, another NPC), LOG it and consider how to interact based on your goals.
"""

    prompt = f"{instructions}\n--- Current World State for Agent {agent_id} (Tick: {tm.tick_counter if tm else 'N/A'}) ---\n{serialized_view}{mem_section}{price_section}\n\nYour Action:"
    return prompt

__all__ = ["build_prompt", "_normalize", "_get_memories"]