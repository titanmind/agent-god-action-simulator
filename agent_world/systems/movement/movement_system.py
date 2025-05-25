
# agent_world/systems/movement/movement_system.py
"""Movement system handling basic velocity-based translation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import logging

from .pathfinding import is_blocked

from ...core.components.position import Position
from ...core.components.physics import Physics
from ...core.components.ai_state import AIState 

logger = logging.getLogger(__name__)


@dataclass
class Velocity:
    """Per-tick delta movement for an entity."""
    dx: int
    dy: int


class MovementSystem:
    """Update entity positions based on attached :class:`Physics` or :class:`Velocity`."""

    def __init__(
        self, world: Any, event_log: List[Dict[str, Any]] | None = None
    ) -> None:
        self.world = world
        self.event_log = event_log if event_log is not None else []

    def update(self, world_obj: Any, tick: int) -> None: 
        em = getattr(world_obj, "entity_manager", None)
        cm = getattr(world_obj, "component_manager", None)
        index = getattr(world_obj, "spatial_index", None)
        size = getattr(world_obj, "size", (0, 0))
        if em is None or cm is None or index is None:
            return

        batch_updates_for_spatial_index: list[tuple[int, tuple[int, int]]] = []

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            ai_state = cm.get_component(entity_id, AIState) 

            if pos is None:
                continue

            # Reset failure flag at the start of this entity's movement processing for this tick,
            # if it's not related to a previous action's failure that AIReasoningSystem is still considering.
            # AIReasoningSystem is responsible for managing retries based on this flag.
            # MovementSystem just reports the outcome of the *current* move attempt.
            if ai_state:
                 # Default to false, will be set true if move is attempted and fails.
                 # AIReasoning system will consume this flag.
                ai_state.last_action_failed_to_achieve_effect = False


            original_pos_tuple = (pos.x, pos.y)
            dx_intent, dy_intent = 0, 0

            phys = cm.get_component(entity_id, Physics)
            if phys is not None:
                dx_intent = int(round(phys.vx))
                dy_intent = int(round(phys.vy))
            else:
                vel = cm.get_component(entity_id, Velocity)
                if vel is not None:
                    dx_intent, dy_intent = vel.dx, vel.dy
                else:
                    # No velocity source, so no move attempt.
                    # Ensure flag is false if no move was even tried by this system.
                    if ai_state:
                        ai_state.last_action_failed_to_achieve_effect = False
                    continue

            if dx_intent == 0 and dy_intent == 0:
                # No intent to move, so not a "failed" move due to blockage.
                if ai_state:
                    ai_state.last_action_failed_to_achieve_effect = False
                continue 

            new_x = pos.x + dx_intent
            new_y = pos.y + dy_intent
            world_width, world_height = size

            move_blocked_by_obstacle_or_boundary = False
            if not (0 <= new_x < world_width and 0 <= new_y < world_height):
                move_blocked_by_obstacle_or_boundary = True
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s intent (%d,%d) to (%d,%d) blocked by boundary.",
                    tick, entity_id, dx_intent, dy_intent, new_x, new_y
                )
            elif is_blocked((new_x, new_y)):
                move_blocked_by_obstacle_or_boundary = True
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s intent (%d,%d) to (%d,%d) blocked by static obstacle.",
                    tick, entity_id, dx_intent, dy_intent, new_x, new_y
                )
            
            if move_blocked_by_obstacle_or_boundary:
                if ai_state:
                    ai_state.last_action_failed_to_achieve_effect = True
                    logger.debug(
                        "[Tick %s] MovementSystem: Entity %s move intent failed (obstacle/boundary); AIState.last_action_failed_to_achieve_effect set to True",
                        tick, entity_id
                    )
                # If physics was driving, PhysicsSystem should zero velocities.
                # If Velocity comp, it's consumed.
                continue 

            # Check for entity collision only if not blocked by static obstacles/boundary
            occupants_at_target = index.query_radius((new_x, new_y), 0)
            is_occupied_by_other = any(occ_id != entity_id for occ_id in occupants_at_target)
            
            if is_occupied_by_other:
                if ai_state:
                    ai_state.last_action_failed_to_achieve_effect = True
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s intent (%d,%d) to (%d,%d) blocked by other entity. Occupants: %s. Flag set: %s",
                    tick, entity_id, dx_intent, dy_intent, new_x, new_y, occupants_at_target,
                    ai_state.last_action_failed_to_achieve_effect if ai_state else "N/A"
                )
                if self.event_log is not None:
                    self.event_log.append({
                        "type": "move_blocked_by_entity", "entity": entity_id,
                        "target_pos": (new_x, new_y), "occupants": occupants_at_target,
                        "tick": tick
                    })
                continue # Don't update position if blocked by another entity

            # If all checks pass, update position
            pos.x = new_x
            pos.y = new_y
            if ai_state:
                ai_state.last_action_failed_to_achieve_effect = False # Successful move
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s successful move from %s to (%s,%s). AIState.last_action_failed_to_achieve_effect set to False",
                    tick, entity_id, original_pos_tuple, pos.x, pos.y
                )

            if original_pos_tuple != (pos.x, pos.y):
                # This log is now redundant if the one above for successful move is active.
                # logger.debug(
                #     "[Tick %s] MovementSystem: Entity %s moved from %s to (%s,%s)",
                #     tick, entity_id, original_pos_tuple, pos.x, pos.y
                # )
                batch_updates_for_spatial_index.append((entity_id, (pos.x, pos.y)))

        if batch_updates_for_spatial_index:
            for entity_id_moved, _ in batch_updates_for_spatial_index:
                index.remove(entity_id_moved) 
            index.insert_many(batch_updates_for_spatial_index)

__all__ = ["Velocity", "MovementSystem"]