# agent_world/systems/ai/behavior_tree_system.py
from __future__ import annotations

from typing import Any, Dict
import logging

from ...core.components.ai_state import AIState
from ...core.components.role import RoleComponent
from .behavior_tree import BehaviorTree, build_fallback_tree
from .actions import parse_action_string, ActionQueue 
# Import TimeManager for type hinting if needed, or just access via world
# from ...core.time_manager import TimeManager 


logger = logging.getLogger(__name__)

class BehaviorTreeSystem:
    """Run behaviour trees for agents based on their role."""

    def __init__(
        self,
        world: Any,
        role_trees: Dict[str, BehaviorTree] | None = None,
        default_tree: BehaviorTree | None = None,
    ) -> None:
        self.world = world
        self.role_trees: Dict[str, BehaviorTree] = role_trees or {}
        self.default_tree = default_tree or build_fallback_tree()
        self.action_queue: ActionQueue | None = getattr(world, "action_queue", None)


    def register_tree(self, role: str, tree: BehaviorTree) -> None:
        self.role_trees[role] = tree

    def update(self, tick: int) -> None: # tick is passed by SystemsManager
        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        # FIX: Access TimeManager from self.world
        tm = getattr(self.world, "time_manager", None) 
        
        if self.action_queue is None: 
            self.action_queue = getattr(self.world, "action_queue", None)
            if self.action_queue is None:
                logger.critical("[BehaviorTreeSystem] CRITICAL: ActionQueue not found in world during update. Cannot enqueue BT actions.")
                return

        if em is None or cm is None:
            return

        for entity_id in list(em.all_entities.keys()):
            ai_comp = cm.get_component(entity_id, AIState)
            if ai_comp is None: 
                continue 
            
            role_comp = cm.get_component(entity_id, RoleComponent)
            
            if not (role_comp and not role_comp.uses_llm):
                continue 

            current_role_name = role_comp.role_name 
            tree_to_run = self.role_trees.get(current_role_name, self.default_tree)
            
            if tree_to_run is self.default_tree and current_role_name not in self.role_trees:
                 logger.debug(
                    "[Tick %s][BT System] Agent %s (Role: %s, uses_llm:False) using default BT as no specific tree registered.",
                    tick, entity_id, current_role_name
                )
            
            action_string = tree_to_run.run(entity_id, self.world)
            if action_string:
                logger.info( 
                    "[Tick %s][BT System] Agent %s (Role: %s, uses_llm:False) BT produced action: '%s'",
                    tick, entity_id, current_role_name, action_string
                )
                parsed_actions_list = parse_action_string(entity_id, action_string)
                for act_obj in parsed_actions_list:
                    if self.action_queue: 
                        self.action_queue._queue.append(act_obj)
                    else:
                        logger.error("[BehaviorTreeSystem] ActionQueue became None during update. Lost action: %s", act_obj)
                
                # Update cooldown tick for BT actions.
                # 'tm' is now defined from self.world earlier in the update method.
                # 'tick' is also available directly as a parameter.
                # Using 'tick' passed to update for consistency.
                ai_comp.last_llm_action_tick = tick


__all__ = ["BehaviorTreeSystem"]