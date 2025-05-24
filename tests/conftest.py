import hashlib
from pathlib import Path
import pytest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agent_world.systems.ability.ability_system as ability_system


@pytest.fixture(autouse=True, scope="session")
def patch_ability_module_name():
    original = ability_system.AbilitySystem._module_name

    def _module_name(path: Path) -> str:
        try:
            rel = path.relative_to(path.parents[2])
            base = ".".join(["agent_world"] + list(rel.with_suffix("").parts))
            h = hashlib.md5(str(path).encode("utf-8")).hexdigest()
            return f"{base}_{h}"
        except Exception:
            return original(path)

    ability_system.AbilitySystem._module_name = staticmethod(_module_name)
    yield
    ability_system.AbilitySystem._module_name = original
