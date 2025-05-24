from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.systems.ability.ability_system import AbilitySystem


def test_melee_strike_loaded():
    world = World((5, 5))
    system = AbilitySystem(world)
    assert "MeleeStrike" in system.abilities
