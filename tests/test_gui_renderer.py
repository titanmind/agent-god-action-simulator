from PIL import Image
import pygame

from agent_world.gui.renderer import Renderer
from agent_world.gui.window import Window
from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position
from agent_world.utils.asset_generation import sprite_gen


class DummyWindow(Window):
    def __init__(self) -> None:
        self.sprites = []
        self.text = []

    def draw_sprite(self, entity_id: int, x: int, y: int, pil_image: Image.Image) -> None:
        self.sprites.append((entity_id, x, y))

    def draw_text(self, text: str, x: int, y: int, colour=(255, 255, 255)) -> None:
        self.text.append(text)

    def refresh(self) -> None:  # pragma: no cover - not used
        pass


def _make_world() -> World:
    w = World((10, 10))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    eid = w.entity_manager.create_entity()
    w.component_manager.add_component(eid, Position(2, 3))
    return w


def test_renderer_draws_entities(monkeypatch):
    world = _make_world()
    window = DummyWindow()
    renderer = Renderer(window)
    monkeypatch.setattr(sprite_gen, "get_sprite", lambda eid: Image.new("RGB", (1, 1)))
    monkeypatch.setattr(pygame.event, "get", lambda: [])
    renderer.update(world)
    assert len(window.sprites) == 1


def test_renderer_input_pan_zoom(monkeypatch):
    world = _make_world()
    window = DummyWindow()
    renderer = Renderer(window)
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
        pygame.event.Event(pygame.MOUSEWHEEL, y=1),
    ]
    monkeypatch.setattr(sprite_gen, "get_sprite", lambda eid: Image.new("RGB", (1, 1)))
    monkeypatch.setattr(pygame.event, "get", lambda: events)
    renderer.update(world)
    assert renderer.center[0] > 0
    assert renderer.zoom > 1.0

