import types
from pathlib import Path

import pytest

from agent_world.core.systems_manager import SystemsManager
from agent_world.utils.cli.command_parser import parse_command
from agent_world.utils.cli import commands


def test_parse_command_basic():
    cmd = parse_command("/save foo.json")
    assert cmd is not None
    assert cmd.name == "save"
    assert cmd.args == ["foo.json"]


def test_parse_command_invalid():
    assert parse_command("hello") is None


def test_pause_and_step_flags():
    state = {"paused": False, "step": False}
    commands.pause(state)
    assert state["paused"] is True
    commands.step(state)
    assert state["step"] is True


def test_save_invokes_save_world(monkeypatch, tmp_path: Path):
    called = {}

    def dummy_save_world(world, path):
        called["path"] = Path(path)

    monkeypatch.setattr(commands, "save_world", dummy_save_world)
    world = object()
    path = tmp_path / "world.json"
    commands.save(world, path)
    assert called["path"] == path


def test_reload_abilities_calls_update():
    class DummyAbilitySystem:
        def __init__(self):
            self.called = False
            self.abilities = {}

        def update(self):
            self.called = True

    sys = DummyAbilitySystem()
    mgr = SystemsManager()
    mgr.register(sys)
    world = types.SimpleNamespace(systems_manager=mgr)
    commands.reload_abilities(world)
    assert sys.called


def test_profile_passes_args(monkeypatch):
    called = {}

    def dummy_profile(world, ticks):
        called["world"] = world
        called["ticks"] = ticks

    monkeypatch.setattr(commands, "profile_ticks", dummy_profile)
    world = object()
    commands.profile(world, 5)
    assert called == {"world": world, "ticks": 5}
