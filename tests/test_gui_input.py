import types
import pygame

from agent_world.gui import input as gui_input
from agent_world.systems.ai.actions import ActionQueue, AttackAction, MoveAction, PLAYER_ID
from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.core.spatial.spatial_index import SpatialGrid


def _make_world() -> World:
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    w.spatial_index = SpatialGrid(cell_size=1)
    return w


def test_left_click_attack(monkeypatch):
    world = _make_world()
    world.component_manager.add_component(PLAYER_ID, Position(0, 0))
    world.spatial_index.insert(PLAYER_ID, (0, 0))
    target = world.entity_manager.create_entity()
    world.component_manager.add_component(target, Position(1, 0))
    world.spatial_index.insert(target, (1, 0))

    queue = ActionQueue()
    renderer = types.SimpleNamespace(center=[0.0, 0.0], zoom=1.0)
    events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(32, 0))]
    monkeypatch.setattr(pygame.event, "get", lambda: events)

    gui_input.handle_events(world, renderer, queue, {})
    action = queue.pop()
    assert isinstance(action, AttackAction) and action.target == target


def test_left_click_move_when_far(monkeypatch):
    world = _make_world()
    world.component_manager.add_component(PLAYER_ID, Position(0, 0))
    world.spatial_index.insert(PLAYER_ID, (0, 0))
    target = world.entity_manager.create_entity()
    world.component_manager.add_component(target, Position(3, 0))
    world.spatial_index.insert(target, (3, 0))

    queue = ActionQueue()
    renderer = types.SimpleNamespace(center=[0.0, 0.0], zoom=1.0)
    events = [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(96, 0))]
    monkeypatch.setattr(pygame.event, "get", lambda: events)

    gui_input.handle_events(world, renderer, queue, {})
    action = queue.pop()
    assert isinstance(action, MoveAction) and action.dx == 1


def test_hotkeys(monkeypatch):
    world = types.SimpleNamespace(time_manager=object())
    queue = ActionQueue()
    renderer = types.SimpleNamespace(center=[0.0, 0.0], zoom=1.0)
    state = {"paused": False}
    calls = {}
    monkeypatch.setattr(gui_input.commands, "reload_abilities", lambda w: calls.setdefault("r", True))
    monkeypatch.setattr(gui_input.observer, "install_tick_observer", lambda tm: calls.setdefault("i", True))
    monkeypatch.setattr(gui_input.observer, "toggle_live_fps", lambda: calls.setdefault("f", True))
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r),
    ]
    monkeypatch.setattr(pygame.event, "get", lambda: events)

    gui_input.handle_events(world, renderer, queue, state)
    assert state["paused"] is True
    assert state["fps"] is True
    assert calls == {"i": True, "f": True, "r": True}
    assert queue.pop() is None
