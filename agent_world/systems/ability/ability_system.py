
"""Dynamic ability loader and executor."""

from __future__ import annotations

import hashlib
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import inspect
from types import ModuleType
from typing import Any, Dict, List, Sequence, Optional # Added Optional for type hint

from ...abilities.base import Ability
from .cooldowns import CooldownManager
import logging # For more structured logging

logger = logging.getLogger(__name__)

class AbilitySystem:
    """Load, hot-reload and execute ability modules."""

    def __init__(self, world: Any, search_dirs: Sequence[Path] | None = None) -> None:
        self.world = world
        base_dir = Path(__file__).resolve().parents[2] / "abilities"
        builtin_dir = base_dir / "builtin"
        generated_dir = base_dir / "generated"
        
        # Ensure generated directory exists
        generated_dir.mkdir(parents=True, exist_ok=True)

        self.search_dirs: List[Path] = (
            list(search_dirs) if search_dirs is not None else [builtin_dir, generated_dir]
        )
        logger.info(f"AbilitySystem initialized. Searching for abilities in: {self.search_dirs}")

        self._modules: Dict[Path, ModuleType] = {}
        self._mtimes: Dict[Path, float] = {}
        self._hashes: Dict[Path, str] = {}
        self.abilities: Dict[str, Ability] = {} # Stores Ability instances
        self.cooldowns = CooldownManager()

        self._load_all()

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _module_name(path: Path) -> str:
        """Return a unique module name for ``path``."""
        # Using a simpler unique name based on path parts to be more readable
        # And still unique enough for this context.
        # Example: abilities.generated.my_heal -> ability_generated_my_heal
        # Example: abilities.builtin.melee -> ability_builtin_melee
        relative_path_parts = path.parts[path.parts.index('abilities'):]
        module_name_str = "_".join(relative_path_parts).replace('.py', '')
        # Sanitize for module name (Python identifiers)
        module_name_str = "".join(c if c.isalnum() else '_' for c in module_name_str)
        return f"agent_ability_module_{module_name_str}"


    def _load_module(self, path: Path) -> None:
        try:
            data = path.read_bytes()
            digest = hashlib.md5(data).hexdigest()
            mtime = path.stat().st_mtime

            # Check if module needs reloading
            needs_load = (
                path not in self._mtimes or 
                self._mtimes[path] != mtime or 
                self._hashes[path] != digest
            )

            if not needs_load:
                return # No change, skip loading

            module_name = self._module_name(path)
            
            # If module was loaded before, clear its old abilities before reload
            if path in self._modules:
                old_module = self._modules[path]
                for name, ability_instance in list(self.abilities.items()):
                    if ability_instance.__class__.__module__ == old_module.__name__:
                        logger.info(f"Unregistering old ability '{name}' from module {old_module.__name__}")
                        del self.abilities[name]
            
            logger.info(f"Loading ability module from: {path} as {module_name}")
            loader = SourceFileLoader(module_name, str(path))
            spec = spec_from_loader(loader.name, loader)
            if spec is None:
                logger.error(f"Could not create spec for module {path}")
                return
            
            module = module_from_spec(spec) # Create a new module object
            loader.exec_module(module) # Execute module code in this new module object

            self._modules[path] = module
            self._mtimes[path] = mtime
            self._hashes[path] = digest
            self._register_module_abilities(module, path) # Pass path for logging context
        except FileNotFoundError:
            logger.warning(f"Ability file {path} not found during load (possibly deleted).")
            if path in self._modules: del self._modules[path]
            if path in self._mtimes: del self._mtimes[path]
            if path in self._hashes: del self._hashes[path]
        except Exception as e:
            logger.error(f"Error loading ability module {path}: {e}", exc_info=True)


    def _register_module_abilities(self, module: ModuleType, module_path: Path) -> None:
        found_any = False
        for name, obj in module.__dict__.items():
            if inspect.isclass(obj) and issubclass(obj, Ability) and obj is not Ability:
                try:
                    ability_instance = obj() # Instantiate the ability
                    ability_key = obj.__name__ # Use class name as key
                    if ability_key in self.abilities:
                        logger.warning(f"Ability '{ability_key}' from {module_path} conflicts with an existing ability. Overwriting.")
                    self.abilities[ability_key] = ability_instance
                    logger.info(f"Registered ability: '{ability_key}' from module {module.__name__} (path: {module_path})")
                    found_any = True
                except Exception as e:
                    logger.error(f"Error instantiating ability class {name} from {module_path}: {e}", exc_info=True)
        if not found_any:
            logger.debug(f"No ability classes found in module {module_path}")


    def _load_all(self) -> None:
        """Scans search directories and loads/reloads ability modules."""
        current_module_paths = set()
        for dir_path in self.search_dirs:
            if not dir_path.exists():
                # logger.warning(f"Ability search directory not found: {dir_path}") # Can be verbose
                continue
            for path in dir_path.glob("*.py"):
                if path.name == "__init__.py": continue # Skip __init__.py files
                current_module_paths.add(path)
                self._load_module(path)
        
        # Unload modules for files that were deleted
        deleted_paths = set(self._modules.keys()) - current_module_paths
        for path in deleted_paths:
            logger.info(f"Ability file {path} seems to be deleted. Unloading associated abilities.")
            old_module = self._modules.pop(path, None)
            if old_module:
                 for name, ability_instance in list(self.abilities.items()):
                    if ability_instance.__class__.__module__ == old_module.__name__:
                        logger.info(f"Unregistering deleted ability '{name}' from module {old_module.__name__}")
                        del self.abilities[name]
            self._mtimes.pop(path, None)
            self._hashes.pop(path, None)


    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def update(self) -> None: # Called by SystemsManager
        """Hot-reload modified abilities and advance cooldowns."""
        self.cooldowns.tick()
        self._load_all() # This will scan for new/modified files

    # ------------------------------------------------------------------
    # Ability usage
    # ------------------------------------------------------------------
    def use(self, ability_name: str, caster_id: int, target_id: Optional[int] = None) -> bool:
        """Attempt to use ``ability_name`` for ``caster_id``."""
        ability = self.abilities.get(ability_name)
        if ability is None:
            logger.warning(f"Agent {caster_id} tried to use unknown ability: '{ability_name}'")
            return False
        
        if not self.cooldowns.available(caster_id, ability_name):
            logger.debug(f"Ability '{ability_name}' on cooldown for agent {caster_id}.")
            return False
        
        try:
            if not ability.can_use(caster_id, self.world, target_id):
                logger.debug(f"Agent {caster_id} cannot use ability '{ability_name}' (can_use returned False).")
                return False
        except Exception as e:
            logger.error(f"Error in can_use for ability '{ability_name}' by agent {caster_id}: {e}", exc_info=True)
            return False

        try:
            ability.execute(caster_id, self.world, target_id)
            self.cooldowns.set_cooldown(caster_id, ability_name, ability.cooldown)
            logger.info(f"Agent {caster_id} used ability '{ability_name}' (Target: {target_id}). Cooldown set to {ability.cooldown}.")
            return True
        except Exception as e:
            logger.error(f"Error in execute for ability '{ability_name}' by agent {caster_id}: {e}", exc_info=True)
            return False


__all__ = ["AbilitySystem"]