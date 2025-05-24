from agent_world.gui.renderer import Renderer


def test_center_on_entity_stub():
    renderer = Renderer.__new__(Renderer)
    assert renderer.center_on_entity(1) is None
