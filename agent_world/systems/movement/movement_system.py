
# agent-god-action-simulator/agent_world/systems/movement/movement_system.py
"""Movement system handling basic velocity-based translation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import logging

from .pathfinding import is_blocked

from ...core.components.position import Position
from ...core.components.physics import Physics
from ...core.components.ai_state import AIState # <<< ADDED for last_bt_move_failed

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

    def update(self, world_obj: Any, tick: int) -> None: # Added world_obj and tick to match SystemManager call
        """Move all entities with ``Position`` and a velocity source."""
        # tm = getattr(self.world, "time_manager", None) # world_obj passed in
        # current_tick = tm.tick_counter if tm else "N/A" # Use tick passed in

        em = getattr(world_obj, "entity_manager", None)
        cm = getattr(world_obj, "component_manager", None)
        index = getattr(world_obj, "spatial_index", None)
        size = getattr(world_obj, "size", (0, 0))
        if em is None or cm is None or index is None:
            return

        batch_updates_for_spatial_index: list[tuple[int, tuple[int, int]]] = []

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            ai_state = cm.get_component(entity_id, AIState) # Get AIState for the flag

            if pos is None:
                continue

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
                    if ai_state: # If no velocity source but has AIState, it means no move was attempted
                        ai_state.last_bt_move_failed = False # Reset flag if no move was even tried
                    continue

            if dx_intent == 0 and dy_intent == 0:
                if ai_state: # No intent to move, so not a "failed" move
                    ai_state.last_bt_move_failed = False
                continue 

            new_x = pos.x + dx_intent
            new_y = pos.y + dy_intent
            world_width, world_height = size

            move_blocked = False
            if not (0 <= new_x < world_width and 0 <= new_y < world_height):
                move_blocked = True
                logger.warning(
                    "[Tick %s] MovementSystem: Entity %s blocked by boundary",
                    tick,
                    entity_id,
                )
            elif is_blocked((new_x, new_y)):
                move_blocked = True
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s blocked by static obstacle at (%s,%s)",
                    tick,
                    entity_id,
                    new_x,
                    new_y,
                )
            else:
                occupants_at_target = index.query_radius((new_x, new_y), 0)
                is_occupied_by_other = any(occ_id != entity_id for occ_id in occupants_at_target)
                if is_occupied_by_other:
                    move_blocked = True
                    logger.info(
                        "[Tick %s] MovementSystem: Entity %s blocked by other entity at (%s,%s). Occupants: %s",
                        tick,
                        entity_id,
                        new_x,
                        new_y,
                        occupants_at_target,
                    )
                    if self.event_log is not None:
                        self.event_log.append({
                            "type": "move_blocked_by_entity", "entity": entity_id,
                            "target_pos": (new_x, new_y), "occupants": occupants_at_target,
                            "tick": tick
                        })
            
            if move_blocked:
                if ai_state:
                    ai_state.last_bt_move_failed = True
                    logger.debug(
                        "[Tick %s] MovementSystem: Entity %s move failed; AIState.last_bt_move_failed set to True",
                        tick,
                        entity_id,
                    )
                # If movement from physics was blocked, PhysicsSystem should handle zeroing vx/vy.
                # If from Velocity comp, this just prevents the move.
                continue # Don't update position

            # If all checks pass, update position
            pos.x = new_x
            pos.y = new_y
            if ai_state:  # Successful move
                ai_state.last_bt_move_failed = False
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s successful move. AIState.last_bt_move_failed set to False",
                    tick,
                    entity_id,
                )


            if original_pos_tuple != (pos.x, pos.y):
                logger.debug(
                    "[Tick %s] MovementSystem: Entity %s moved from %s to (%s,%s)",
                    tick,
                    entity_id,
                    original_pos_tuple,
                    pos.x,
                    pos.y,
                )
                batch_updates_for_spatial_index.append((entity_id, (pos.x, pos.y)))

        if batch_updates_for_spatial_index:
            for entity_id_moved, _ in batch_updates_for_spatial_index:
                index.remove(entity_id_moved) 
            index.insert_many(batch_updates_for_spatial_index)


__all__ = ["Velocity", "MovementSystem"]