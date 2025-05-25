from __future__ import annotations

"""Abstract planner interface."""

from abc import ABC, abstractmethod
from typing import Any, List

# ``ActionStep`` includes an optional ``step_type`` field used by planners in
# Phase 11.5 and later.
from ...core.components.ai_state import Goal, ActionStep


class BasePlanner(ABC):
    """Base class for planning algorithms."""

    @abstractmethod
    def create_plan(
        self, agent_id: int, goals: List[Goal], world: Any
    ) -> List[ActionStep]:
        """Return a plan of action steps for ``agent_id``."""
        raise NotImplementedError


__all__ = ["BasePlanner"]
