"""Track ability class names already granted to an entity."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnownAbilitiesComponent:
    """Simple list of ability class names available to an entity."""

    known_class_names: list[str] = field(default_factory=list)


__all__ = ["KnownAbilitiesComponent"]
