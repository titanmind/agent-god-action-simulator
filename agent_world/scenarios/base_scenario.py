from abc import ABC, abstractmethod
from typing import Any


class BaseScenario(ABC):
    """Abstract base class for gameplay scenarios."""

    @abstractmethod
    def setup(self, world: Any) -> None:
        """Populate the world with scenario entities and state."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return a human readable name for the scenario."""
        pass
