"""Angel system stub."""

from __future__ import annotations

from typing import Any


class AngelSystem:
    """Stub placeholder for future Angel functionality."""

    def __init__(self, world: Any) -> None:
        self.world = world

    def generate_and_grant(self, agent_id: int, description: str) -> dict:
        """Stub ability generation and granting."""
        return {"status": "stub"}


def get_angel_system(world: Any) -> AngelSystem:
    """Return existing AngelSystem instance on world or create one."""
    if not hasattr(world, "angel_system_instance") or world.angel_system_instance is None:
        world.angel_system_instance = AngelSystem(world)
    return world.angel_system_instance


__all__ = ["AngelSystem", "get_angel_system"]
