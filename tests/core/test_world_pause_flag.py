import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.components.ai_state import AIState


def test_world_paused_for_angel_default():
    world = World((5, 5))
    assert world.paused_for_angel is False


def test_ai_state_needs_immediate_rethink_default():
    state = AIState(personality="tester")
    assert state.needs_immediate_rethink is False
