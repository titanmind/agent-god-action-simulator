"""Dynamic ability loader and executor."""

from __future__ import annotations

import hashlib
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import inspect
from types import ModuleType
from typing import Any, Dict, List, Sequence

from ...abilities.base import Ability
from .cooldowns import CooldownManager


class AbilitySystem:
    """Load, hot-reload and execute ability modules."""

    def __init__(self, world: Any, search_dirs: Sequence[Path] | None = None) -> None:
        self.world = world
        base_dir = Path(__file__).resolve().parents[2] / "abilities"
        builtin = base_dir / "builtin"
        generated = base_dir / "generated"
        self.search_dirs: List[Path] = (
            list(search_dirs) if search_dirs else [builtin, generated]
        )

        self._modules: Dict[Path, ModuleType] = {}
        self._mtimes: Dict[Path, float] = {}
        self._hashes: Dict[Path, str] = {}
        self.abilities: Dict[str, Ability] = {}
        self.cooldowns = CooldownManager()

        self._load_all()

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _module_name(path: Path) -> str:
        """Return a unique module name for ``path``."""

        h = hashlib.md5(str(path).encode("utf-8")).hexdigest()
        return f"ability_{path.stem}_{h}"

    def _load_module(self, path: Path) -> None:
        data = path.read_bytes()
        digest = hashlib.md5(data).hexdigest()
        mtime = path.stat().st_mtime
        if self._mtimes.get(path) == mtime and self._hashes.get(path) == digest:
            return

        loader = SourceFileLoader(self._module_name(path), str(path))
        spec = spec_from_loader(loader.name, loader)
        if spec is None:
            return
        module = module_from_spec(spec)
        loader.exec_module(module)

        self._modules[path] = module
        self._mtimes[path] = mtime
        self._hashes[path] = digest
        self._register_module(module)

    def _register_module(self, module: ModuleType) -> None:
        for obj in module.__dict__.values():
            if inspect.isclass(obj) and issubclass(obj, Ability) and obj is not Ability:
                self.abilities[obj.__name__] = obj()

    def _load_all(self) -> None:
        for d in self.search_dirs:
            if not d.exists():
                continue
            for path in d.glob("*.py"):
                self._load_module(path)

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def update(self) -> None:
        """Hot-reload modified abilities and advance cooldowns."""

        self.cooldowns.tick()
        self._load_all()

    # ------------------------------------------------------------------
    # Ability usage
    # ------------------------------------------------------------------
    def use(self, ability_name: str, caster_id: int) -> bool:
        """Attempt to use ``ability_name`` for ``caster_id``."""

        ability = self.abilities.get(ability_name)
        if ability is None:
            return False
        if not self.cooldowns.available(caster_id, ability_name):
            return False
        if not ability.can_use(caster_id, self.world):
            return False

        ability.execute(caster_id, self.world)
        self.cooldowns.set_cooldown(caster_id, ability_name, ability.cooldown)
        return True


__all__ = ["AbilitySystem"]
