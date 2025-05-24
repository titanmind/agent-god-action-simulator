
"""Movement system handling basic velocity-based translation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .pathfinding import is_blocked

from ...core.components.position import Position
from ...core.components.physics import Physics


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

    def update(self) -> None: # SystemsManager calls update(world, tick) or update(tick) or update()
        """Move all entities with ``Position`` and a velocity source."""
        tm = getattr(self.world, "time_manager", None)
        current_tick = tm.tick_counter if tm else "N/A"

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        index = getattr(self.world, "spatial_index", None)
        size = getattr(self.world, "size", (0, 0)) # world.size
        if em is None or cm is None or index is None:
            return

        batch_updates_for_spatial_index: list[tuple[int, tuple[int, int]]] = []

        for entity_id in list(em.all_entities.keys()):
            pos = cm.get_component(entity_id, Position)
            if pos is None:
                continue

            original_pos_tuple = (pos.x, pos.y) # For checking if position changed

            dx_intent, dy_intent = 0, 0 # Initialize movement intent

            # Prioritize Physics component for velocity
            phys = cm.get_component(entity_id, Physics)
            if phys is not None:
                # Movement is based on integer grid steps. Physics velocities are float.
                # Rounding determines if movement occurs.
                # PhysicsSystem already applied friction and collision response to phys.vx/vy.
                dx_intent = int(round(phys.vx)) # Take 1 tick's worth of velocity
                dy_intent = int(round(phys.vy))
                # --- LOGGING: Movement from Physics ---
                # if dx_intent != 0 or dy_intent != 0 : # Log only if there's an intent to move
                #     print(f"[Tick {current_tick}] MovementSystem: Entity {entity_id} from Physics vel ({phys.vx:.2f},{phys.vy:.2f}) -> intent dx={dx_intent}, dy={dy_intent}. Old pos: {original_pos_tuple}")
                # --- END LOGGING ---
            else:
                # Fallback to Velocity component if Physics component is absent
                vel = cm.get_component(entity_id, Velocity)
                if vel is not None:
                    dx_intent, dy_intent = vel.dx, vel.dy
                    # --- LOGGING: Movement from Velocity Comp ---
                    # print(f"[Tick {current_tick}] MovementSystem: Entity {entity_id} from Velocity comp ({vel.dx},{vel.dy}). Old pos: {original_pos_tuple}")
                    # --- END LOGGING ---
                else:
                    continue # No velocity source, no movement

            if dx_intent == 0 and dy_intent == 0:
                continue # No intent to move this tick

            new_x = pos.x + dx_intent
            new_y = pos.y + dy_intent
            world_width, world_height = size

            # Boundary and obstacle checks
            if not (0 <= new_x < world_width and 0 <= new_y < world_height and not is_blocked((new_x, new_y))):
                # --- LOGGING: Movement Blocked (Boundary/Obstacle) ---
                # print(f"[Tick {current_tick}] MovementSystem: Entity {entity_id} movement to ({new_x},{new_y}) blocked (boundary/obstacle). Stays at {original_pos_tuple}")
                # --- END LOGGING ---
                # If movement from physics was blocked, PhysicsSystem should have zeroed vx/vy.
                # If movement from Velocity comp, this just prevents the move.
                continue

            # Check for other entities occupying the target cell (simple collision)
            # Note: Spatial index query for radius 0 gives entities *at* that exact point.
            # This assumes entities cannot occupy the same tile.
            # More complex collision (e.g. entity sizes) would need radius > 0.
            occupants_at_target = index.query_radius((new_x, new_y), 0)
            # Filter out self if it somehow appears in query_radius at new_x, new_y (shouldn't for radius 0 if not there yet)
            is_occupied_by_other = any(occ_id != entity_id for occ_id in occupants_at_target)

            if is_occupied_by_other:
                if self.event_log is not None:
                    self.event_log.append({
                        "type": "move_blocked_by_entity", "entity": entity_id,
                        "target_pos": (new_x, new_y), "occupants": occupants_at_target,
                        "tick": current_tick
                    })
                # --- LOGGING: Movement Blocked (Entity) ---
                # print(f"[Tick {current_tick}] MovementSystem: Entity {entity_id} movement to ({new_x},{new_y}) blocked by other entity/entities: {occupants_at_target}. Stays at {original_pos_tuple}")
                # --- END LOGGING ---
                continue

            # If all checks pass, update position
            pos.x = new_x
            pos.y = new_y

            if original_pos_tuple != (pos.x, pos.y):
                # --- LOGGING: Successful Move ---
                print(f"[Tick {current_tick}] MovementSystem: Entity {entity_id} MOVED from {original_pos_tuple} to ({pos.x},{pos.y})")
                # --- END LOGGING ---
                # No need to remove from spatial index here if we batch update later.
                # If updating one by one: index.remove(entity_id)
                batch_updates_for_spatial_index.append((entity_id, (pos.x, pos.y)))

        # Batch update spatial index after all position changes for this tick
        if batch_updates_for_spatial_index:
            # First remove all entities that moved from their old positions
            for entity_id, _ in batch_updates_for_spatial_index:
                index.remove(entity_id) # remove uses cached old position
            # Then insert them at their new positions
            index.insert_many(batch_updates_for_spatial_index)


__all__ = ["Velocity", "MovementSystem"]