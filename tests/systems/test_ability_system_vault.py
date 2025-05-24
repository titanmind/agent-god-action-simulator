import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.systems.ability.ability_system import AbilitySystem


def test_vault_abilities_loaded_by_default():
    world = World((5, 5))
    system = AbilitySystem(world)
    assert "SampleFireball" in system.abilities
