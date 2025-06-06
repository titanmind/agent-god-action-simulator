
from __future__ import annotations

"""Base interface for dynamic abilities."""

from abc import ABC, abstractmethod
from typing import Any, Optional # <<< ADDED Optional

class Ability(ABC):
    """Abstract base class for all abilities."""

    @property
    @abstractmethod
    def energy_cost(self) -> int:
        """Energy consumed when the ability is used."""
        raise NotImplementedError

    @property
    @abstractmethod
    def cooldown(self) -> int:
        """Number of ticks before the ability can be used again."""
        raise NotImplementedError

    @abstractmethod
    def can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> bool: # <<< ADDED target_id
        """Return ``True`` if ``caster_id`` is able to use the ability."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, caster_id: int, world: Any, target_id: Optional[int] = None) -> None: # <<< ADDED target_id
        """Perform the ability's action on ``world``."""
        raise NotImplementedError


__all__ = ["Ability"]