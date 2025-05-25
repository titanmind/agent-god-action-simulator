from __future__ import annotations

from typing import Any

from .base_scenario import BaseScenario
from ..utils.cli import commands
from ..core.components.ai_state import AIState
from ..core.components.position import Position
from ..systems.movement.pathfinding import set_obstacles, clear_obstacles


class DefaultPickupScenario(BaseScenario):
    """Basic scenario where an agent must pick up a nearby item."""

    def get_name(self) -> str:
        return "Default Pickup"

    def setup(self, world: Any) -> None:
        """Spawn an agent and item with a blocking obstacle."""

        clear_obstacles()

        center_x = world.size[0] // 2
        center_y = world.size[1] // 2

        agent_id = commands.spawn(world, "npc", str(center_x), str(center_y))
        item_x = center_x
        item_y = center_y - 2
        item_id = commands.spawn(world, "item", str(item_x), str(item_y))

        if agent_id and item_id and world.component_manager:
            ai_state = world.component_manager.get_component(agent_id, AIState)
            if ai_state:
                from ..core.components.ai_state import Goal
                ai_state.goals = [Goal(type="Acquire item", target=item_id)]
                print(
                    f"[Scenario] Agent {agent_id} at ({center_x},{center_y}) given goal: {ai_state.goals}"
                )
            item_pos = world.component_manager.get_component(item_id, Position)
            if item_pos:
                print(
                    f"[Scenario] Item {item_id} spawned at ({item_pos.x},{item_pos.y}) for Agent {agent_id}."
                )
            else:
                print(
                    f"[Scenario WARNING] Item {item_id} spawned but has no Position component!"
                )

        obstacle_pos = (center_x, center_y - 1)
        set_obstacles([obstacle_pos])
        print(f"[Scenario] Obstacle placed at {obstacle_pos}")
