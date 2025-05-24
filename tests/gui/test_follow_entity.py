import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.gui.renderer import Renderer
from agent_world.core.world import World
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.position import Position


def test_center_on_entity_updates_camera():
    world = World((10, 10))
    world.component_manager = ComponentManager()
    entity_id = 42
    world.component_manager.add_component(entity_id, Position(7, 3))

    renderer = Renderer.__new__(Renderer)
    renderer.camera_world_x = 0.0
    renderer.camera_world_y = 0.0
    renderer._last_world = world

    renderer.center_on_entity(entity_id)

    assert renderer.camera_world_x == 7.0
    assert renderer.camera_world_y == 3.0


