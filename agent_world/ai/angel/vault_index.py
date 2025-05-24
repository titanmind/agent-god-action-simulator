from __future__ import annotations

"""Utility for indexing ability vault modules."""

from dataclasses import dataclass, field
from importlib import util as importlib_util
from pathlib import Path
from typing import Dict

from agent_world.abilities.base import Ability


@dataclass
class VaultIndex:
    """Simple keyword lookup for abilities defined in the vault."""

    keyword_to_class: Dict[str, str] = field(default_factory=dict)
    built: bool = False

    def build(self) -> None:
        if self.built:
            return
        base_dir = Path(__file__).resolve().parents[2] / "abilities" / "vault"
        for path in base_dir.glob("*.py"):
            if path.name == "__init__.py":
                continue
            spec = importlib_util.spec_from_file_location(f"vault_{path.stem}", path)
            if spec is None or spec.loader is None:
                continue
            module = importlib_util.module_from_spec(spec)
            spec.loader.exec_module(module)
            metadata = getattr(module, "METADATA", {})
            tags = [str(t).lower() for t in metadata.get("tags", [])]
            description = str(metadata.get("description", "")).lower()
            ability_class_name = None
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and issubclass(obj, Ability) and obj is not Ability:
                    ability_class_name = obj.__name__
                    break
            if ability_class_name:
                for key in tags + [description]:
                    if key:
                        self.keyword_to_class.setdefault(key, ability_class_name)
        self.built = True

    def lookup(self, description: str) -> str | None:
        if not self.built:
            self.build()
        return self.keyword_to_class.get(description.strip().lower())


_vault_index: VaultIndex | None = None


def get_vault_index() -> VaultIndex:
    global _vault_index
    if _vault_index is None:
        _vault_index = VaultIndex()
        _vault_index.build()
    return _vault_index

__all__ = ["VaultIndex", "get_vault_index"]
