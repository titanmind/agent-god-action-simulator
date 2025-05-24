import types
from pathlib import Path

import pytest

from agent_world.core.systems_manager import SystemsManager
from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
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


def _make_world():
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    return w


def test_spawn_npc_and_item():
    world = _make_world()
    npc = commands.spawn(world, "npc")
    item = commands.spawn(world, "item")
    assert npc is not None and item is not None
    cm = world.component_manager
    assert cm.get_component(npc, Position) is not None
    assert cm.get_component(item, Position) is not None


def test_debug_outputs_components(capsys):
    world = _make_world()
    ent = commands.spawn(world, "npc")
    commands.debug(world, ent)
    out = capsys.readouterr().out
    assert "Position" in out

