
"""Utilities for constructing deterministic LLM prompts."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, List, Set, Dict 

import threading
import asyncio

from ...core.world import World
from ...core.components.position import Position
from ...core.components.health import Health # For visible entities
from ...core.components.ai_state import AIState # For visible NPCs' personality
from ...core.components.perception_cache import PerceptionCache # To get visible entities
from ...systems.interaction.pickup import Tag # For identifying items
from ...systems.interaction.trading import get_local_prices
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
        if is_dataclass(obj) and not isinstance(obj, type): # ensure it's an instance
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
                "num_entities": len(obj.entity_manager.all_entities) if obj.entity_manager else 0,
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


def build_prompt(agent_id: int, world_view: Any, *, memory_k: int = 5) -> str:
    global _VISITED_OBJECTS_DURING_NORMALIZE
    _VISITED_OBJECTS_DURING_NORMALIZE = set() 

    agent_specific_world_data: Dict[str, Any] = {}

    if isinstance(world_view, World):
        em = world_view.entity_manager
        cm = world_view.component_manager
        tm = world_view.time_manager

        agent_specific_world_data["world_info"] = {
            "size": world_view.size,
            "current_tick": tm.tick_counter if tm else -1,
        }
        
        agent_components_dict: Dict[str, Any] = {}
        if em and cm and em.has_entity(agent_id):
            raw_components = cm._components.get(agent_id, {}) if hasattr(cm, '_components') else {}
            for comp_name_type, comp_instance in raw_components.items():
                comp_name = comp_name_type.__name__ if isinstance(comp_name_type, type) else str(comp_name_type)
                _VISITED_OBJECTS_DURING_NORMALIZE = set()
                # Exclude PerceptionCache from "my_components" as it's handled separately
                if not isinstance(comp_instance, PerceptionCache):
                     agent_components_dict[comp_name] = _normalize(comp_instance)
        agent_specific_world_data["my_components"] = agent_components_dict

        # --- Incorporate Perception Data ---
        visible_entities_info = []
        if cm: # Ensure component_manager exists
            perception_cache = cm.get_component(agent_id, PerceptionCache)
            if perception_cache and perception_cache.visible:
                for visible_eid in perception_cache.visible:
                    if not em.has_entity(visible_eid): continue # Should not happen if cache is fresh

                    entity_info: Dict[str, Any] = {"id": visible_eid}
                    
                    v_pos = cm.get_component(visible_eid, Position)
                    if v_pos: entity_info["position"] = _normalize(v_pos)
                    
                    v_health = cm.get_component(visible_eid, Health)
                    if v_health: entity_info["health"] = _normalize(v_health)
                                    
                    v_aistate = cm.get_component(visible_eid, AIState)
                    if v_aistate: entity_info["type"] = "npc"; entity_info["personality_summary"] = v_aistate.personality[:30] # Brief summary
                    
                    v_tag = cm.get_component(visible_eid, Tag)
                    if v_tag: entity_info["type"] = "item"; entity_info["tag"] = v_tag.name

                    if "type" not in entity_info: entity_info["type"] = "unknown"
                    
                    # Limit detail to prevent overly long prompts for many entities
                    visible_entities_info.append(entity_info)
        
        if visible_entities_info:
            agent_specific_world_data["visible_entities"] = visible_entities_info
        else:
            agent_specific_world_data["visible_entities"] = "You see no other entities."
        # --- End Perception Data ---

    else:
        _VISITED_OBJECTS_DURING_NORMALIZE = set()
        agent_specific_world_data["custom_view"] = _normalize(world_view)

    _VISITED_OBJECTS_DURING_NORMALIZE = set()
    normalized_view = _normalize(agent_specific_world_data)
    
    try:
        serialized_view = json.dumps(normalized_view, sort_keys=True, indent=2, default=str)
    except TypeError as e:
        serialized_view = f'{{"error": "Failed to serialize agent world view", "details": "{str(e)}"}}'

    price_section = ""
    if isinstance(world_view, World):
        try:
            cm = world_view.component_manager
            if cm:
                pos = cm.get_component(agent_id, Position)
                if pos:
                    prices = get_local_prices(world_view, (pos.x, pos.y))
                    _VISITED_OBJECTS_DURING_NORMALIZE = set()
                    normalized_prices = _normalize(prices)
                    price_json = json.dumps(normalized_prices, sort_keys=True, indent=2, default=str)
                    price_section = f"\n\nLocal Prices (approximate):\n{price_json}"
        except Exception:
            price_section = "\n\nLocal Prices: <error retrieving prices>"

    memories = _get_memories(agent_id, memory_k)
    mem_section = ""
    if memories:
        try:
            mem_json = json.dumps(memories, sort_keys=True, indent=2)
            mem_section = f"\n\nRecent Memories:\n{mem_json}"
        except TypeError:
            mem_section = "\n\nRecent Memories: <error serializing memories>"

    # --- Updated Prompt Instructions ---
    instructions = f"""You are Agent {agent_id}. Your goal is to explore the world, observe your surroundings, interact with entities, and survive.
You perceive the world through the information provided below. Your world is a grid.

Available Actions (respond with ONLY ONE action string):
- "MOVE <N|S|E|W>": Move one step in the specified cardinal direction. (e.g., "MOVE N")
- "ATTACK <target_id>": Attack a visible entity with the given ID. (e.g., "ATTACK 15")
- "LOG <message>": Record a message in your log. Use this to note observations or thoughts. (e.g., "LOG Found a strange rock.")
- "IDLE": Do nothing for this turn.
- "GENERATE_ABILITY <description>": Request a new ability. Provide a concise description of what you want the ability to do. (e.g., "GENERATE_ABILITY Heal myself for 5 health points")

Current Objective: Explore your surroundings. If you see other entities, consider interacting (e.g., LOG their presence, or ATTACK if hostile - assume neutral unless attacked). If you feel you lack a necessary skill, request it.
"""

    prompt = f"{instructions}\n--- Current World State for Agent {agent_id} ---\n{serialized_view}{mem_section}{price_section}\n\nAction:"
    return prompt

__all__ = ["build_prompt", "_normalize", "_get_memories"]