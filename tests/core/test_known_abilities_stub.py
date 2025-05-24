from agent_world.core.components.known_abilities import KnownAbilitiesComponent


def test_default_known_abilities_state():
    comp = KnownAbilitiesComponent()
    assert comp.known_class_names == []
