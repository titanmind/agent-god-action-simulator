import pytest

from agent_world.core.components.role import RoleComponent
from agent_world.persistence.serializer import serialize, deserialize


def test_role_component_defaults_roundtrip():
    comp = RoleComponent("farmer")
    restored = deserialize(serialize(comp))
    assert isinstance(restored, RoleComponent)
    assert restored.role_name == "farmer"
    assert restored.can_request_abilities is True
    assert restored.uses_llm is True
    assert restored.fixed_abilities == []


def test_role_component_custom_roundtrip():
    original = RoleComponent(
        role_name="wizard",
        can_request_abilities=False,
        uses_llm=False,
        fixed_abilities=["Fireball", "Teleport"],
    )
    restored = deserialize(serialize(original))
    assert isinstance(restored, RoleComponent)
    assert restored.role_name == original.role_name
    assert restored.can_request_abilities == original.can_request_abilities
    assert restored.uses_llm == original.uses_llm
    assert restored.fixed_abilities == original.fixed_abilities
