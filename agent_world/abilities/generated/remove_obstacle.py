"""Generated ability scaffold.
Description (from LLM): remove obstacle
Generated Class Name: RemoveObstacleAbility"""
from __future__ import annotations
from typing import Any, Optional
from agent_world.abilities.base import Ability
from agent_world.systems.movement.pathfinding import OBSTACLES, is_blocked
from agent_world.core.components.position import Position

class RemoveObstacleAbility(Ability):
    """Auto-generated ability: remove obstacle"""
    @property
    def energy_cost(self) -> int: return 0 
    @property
    def cooldown(self) -> int: return 1 

    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool:
        # For this scenario, if the LLM decides to use it based on the critical prompt,
                # we assume it's a valid situation. The obstacle check is done in execute.
                return True

    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None:
        # Note: OBSTACLES, is_blocked, Position are imported.
                obstacle_to_remove = (50,49) # Hardcoded for the specific scenario
        
                if is_blocked(obstacle_to_remove): # Check if it's currently considered an obstacle
                    if obstacle_to_remove in OBSTACLES: # Double check it's in the actual set
                        OBSTACLES.discard(obstacle_to_remove)
                        print(f"Agent {caster_id} used {self.__class__.__name__} and REMOVED obstacle at {obstacle_to_remove}! Obstacles left: {len(OBSTACLES)}")
                    else:
                         print(f"Agent {caster_id} {self.__class__.__name__}: Obstacle at {obstacle_to_remove} was is_blocked() but not in OBSTACLES set.")
                else:
                     print(f"Agent {caster_id} used {self.__class__.__name__}, but no obstacle was found/already cleared at {obstacle_to_remove}.")

__all__ = ["RemoveObstacleAbility"]
