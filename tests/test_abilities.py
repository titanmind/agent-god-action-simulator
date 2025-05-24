import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.abilities.base import Ability
import pytest


class DummyAbility(Ability):
    @property
    def energy_cost(self) -> int:
        return 5

    @property
    def cooldown(self) -> int:
        return 10

    def can_use(self, caster_id: int, world: dict) -> bool:
        return True

    def execute(self, caster_id: int, world: dict) -> None:
        world["executed"] = True


def test_ability_abstract_instantiation():
    with pytest.raises(TypeError):
        Ability()  # type: ignore[abstract]


def test_dummy_ability_usage():
    ability = DummyAbility()
    world: dict = {}
    assert ability.can_use(1, world)
    ability.execute(1, world)
    assert world.get("executed") is True
    assert ability.energy_cost == 5
    assert ability.cooldown == 10
