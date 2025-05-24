"""Role component."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RoleComponent:
    """Define an entity's role and related behaviour flags."""

    role_name: str
    can_request_abilities: bool = True
    uses_llm: bool = True
    fixed_abilities: List[str] = field(default_factory=list)


__all__ = ["RoleComponent"]
