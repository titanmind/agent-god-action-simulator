
"""Integrate forces into velocity and resolve simple collisions."""

from __future__ import annotations

# from dataclasses import dataclass # Force is defined in core.components.force
from typing import Any, Dict, List

from .pathfinding import is_blocked
from ...core.components.position import Position
from ...core.components.physics import Physics
from ...core.components.force import Force # Import Force from components


# @dataclass # This local Force definition is shadowed by the imported one if not careful
# class Force: # This definition is for the component processed BY this system
#     """Instantaneous force applied to an entity for one tick."""
#     fx: float # Using fx, fy to distinguish from component's dx, dy if needed, but component uses dx,dy
#     fy: float


class PhysicsSystem:
    """Update :class:`Physics` components from accumulated :class:`Force` values."""

    def __init__(
        self, world: Any, event_log: List[Dict[str, Any]] | None = None
    ) -> None:
        self.world = world
        self.event_log = event_log if event_log is not None else []

    def update(self) -> None: # SystemsManager calls update(world, tick) or update(tick) or update()
        """Integrate forces and zero velocity on collisions."""
        # Assuming SystemsManager passes tick correctly, or get it from world.time_manager
        tm = getattr(self.world, "time_manager", None)
        current_tick = tm.tick_counter if tm else "N/A"

        em = getattr(self.world, "entity_manager", None)
        cm = getattr(self.world, "component_manager", None)
        size = getattr(self.world, "size", (0, 0))
        if em is None or cm is None:
            return

        width, height = size
        for entity_id in list(em.all_entities.keys()):
            phys = cm.get_component(entity_id, Physics)
            if phys is None:
                continue

            # --- LOGGING: Physics State Before Force ---
            # print(f"[Tick {current_tick}] PhysicsSystem: Entity {entity_id}, Vel BEFORE force processing: ({phys.vx:.2f},{phys.vy:.2f})")
            # --- END LOGGING ---

            # Get the Force component (from core.components.force)
            force_comp = cm.get_component(entity_id, Force) 
            if force_comp is not None:
                # --- LOGGING: Processing Force ---
                print(f"[Tick {current_tick}] PhysicsSystem: Entity {entity_id} processing Force({force_comp.dx},{force_comp.dy}), mass={phys.mass}")
                # --- END LOGGING ---
                
                # Apply impulse: dv = F*dt / m. Since dt=1 tick, dv = F/m.
                # If force_comp.dx/dy are considered impulses (change in momentum), then dv = impulse / m.
                # If force_comp.dx/dy are forces, then a_x = Fx/m, vx += a_x * dt (dt=1 tick)
                phys.vx += force_comp.dx / phys.mass 
                phys.vy += force_comp.dy / phys.mass
                
                force_comp.ttl -= 1
                if force_comp.ttl <= 0:
                    cm.remove_component(entity_id, Force) # Consume the force component after applying
            
            # --- LOGGING: Physics State After Force / Before Collision ---
            # print(f"[Tick {current_tick}] PhysicsSystem: Entity {entity_id}, Vel AFTER force / BEFORE collision: ({phys.vx:.2f},{phys.vy:.2f})")
            # --- END LOGGING ---

            pos = cm.get_component(entity_id, Position)
            if pos is None: # Entity might not have a position, or it's an abstract physical object
                # Apply friction even if no position (e.g., for a projectile in abstract space)
                phys.vx *= phys.friction 
                phys.vy *= phys.friction
                continue

            # Collision detection and response
            # Tentative next position based on current velocity
            # Assuming dt = 1 tick for this calculation
            next_x_float = pos.x + phys.vx 
            next_y_float = pos.y + phys.vy
            next_x_int = int(round(next_x_float)) # Movement system uses int positions
            next_y_int = int(round(next_y_float))

            collision = False
            if (
                next_x_int < 0 or next_x_int >= width or
                next_y_int < 0 or next_y_int >= height or
                is_blocked((next_x_int, next_y_int)) # Check against discrete grid for blockages
            ):
                # --- LOGGING: Collision ---
                print(f"[Tick {current_tick}] PhysicsSystem: Entity {entity_id} COLLIDED. Proposed next_pos_int ({next_x_int},{next_y_int}). Zeroing velocity.")
                # --- END LOGGING ---
                phys.vx = 0.0
                phys.vy = 0.0
                collision = True
                if self.event_log is not None:
                    self.event_log.append(
                        {
                            "type": "collision",
                            "entity": entity_id,
                            "pos": (next_x_int, next_y_int), # Log the cell it would have entered
                            "tick": current_tick
                        }
                    )
            
            # Apply friction after collision resolution (or if no collision)
            if not collision: # Only apply friction if no collision zeroed velocity
                 phys.vx *= phys.friction 
                 phys.vy *= phys.friction
            
            # Clamp very small velocities to zero to prevent endless tiny movements
            if abs(phys.vx) < 0.01: phys.vx = 0.0
            if abs(phys.vy) < 0.01: phys.vy = 0.0

            # --- LOGGING: Physics State End of Tick ---
            # print(f"[Tick {current_tick}] PhysicsSystem: Entity {entity_id}, Vel FINAL for tick: ({phys.vx:.2f},{phys.vy:.2f})")
            # --- END LOGGING ---


__all__ = ["PhysicsSystem"] # Removed local Force to avoid confusion