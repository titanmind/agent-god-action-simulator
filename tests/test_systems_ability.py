from pathlib import Path

from agent_world.systems.ability.ability_system import AbilitySystem
from agent_world.systems.ability.cooldowns import CooldownManager


def test_cooldown_manager_basic():
    cd = CooldownManager()
    cd.set_cooldown(1, "Fireball", 2)
    assert not cd.available(1, "Fireball")
    cd.tick()
    assert not cd.available(1, "Fireball")
    cd.tick()
    assert cd.available(1, "Fireball")


def test_ability_system_load_execute_and_reload(tmp_path: Path):
    ability_code = """from agent_world.abilities.base import Ability

class TempAbility(Ability):
    def can_use(self, caster_id, world):
        return True

    def execute(self, caster_id, world):
        world["count"] = world.get("count", 0) + 1

    @property
    def energy_cost(self):
        return 0

    @property
    def cooldown(self):
        return 1

__all__ = ["TempAbility"]
"""
    ability_path = tmp_path / "temp.py"
    ability_path.write_text(ability_code)

    world: dict = {}
    system = AbilitySystem(world, search_dirs=[tmp_path])
    assert "TempAbility" in system.abilities

    assert system.use("TempAbility", 1)
    assert world.get("count") == 1
    assert not system.use("TempAbility", 1)

    ability_code2 = ability_code.replace("+ 1", "+ 2")
    import time

    time.sleep(1.1)  # ensure mtime difference for reload
    ability_path.write_text(ability_code2)

    system.update()  # tick + reload
    assert system.use("TempAbility", 1)
    assert world.get("count") == 3
