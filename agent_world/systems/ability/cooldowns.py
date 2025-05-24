"""Per-entity cooldown tracking for abilities."""

from __future__ import annotations

from typing import Dict


class CooldownManager:
    """Track remaining cooldown ticks for entity abilities."""

    def __init__(self) -> None:
        # Mapping of entity -> ability -> remaining ticks
        self._cooldowns: Dict[int, Dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_cooldown(self, entity_id: int, ability: str, ticks: int) -> None:
        """Start a cooldown for ``ability`` on ``entity_id`` lasting ``ticks``."""

        if ticks <= 0:
            return
        self._cooldowns.setdefault(entity_id, {})[ability] = ticks

    def available(self, entity_id: int, ability: str) -> bool:
        """Return ``True`` if ``ability`` is not on cooldown for ``entity_id``."""

        return self._cooldowns.get(entity_id, {}).get(ability, 0) <= 0

    def tick(self) -> None:
        """Advance all cooldown timers by one tick."""

        remove_entities: list[int] = []
        for ent, cds in self._cooldowns.items():
            remove_abilities = [name for name, t in cds.items() if t - 1 <= 0]
            for name in remove_abilities:
                cds.pop(name, None)
            for name in list(cds.keys()):
                cds[name] -= 1
            if not cds:
                remove_entities.append(ent)
        for ent in remove_entities:
            self._cooldowns.pop(ent, None)

    def clear_entity(self, entity_id: int) -> None:
        """Remove all cooldowns associated with ``entity_id``."""

        self._cooldowns.pop(entity_id, None)


__all__ = ["CooldownManager"]
