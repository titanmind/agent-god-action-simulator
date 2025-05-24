from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.utils.cli import commands
from agent_world.core.components.role import RoleComponent
from agent_world.core.components.known_abilities import KnownAbilitiesComponent


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.spatial_index = SpatialGrid(1)
    return world


def test_spawn_with_role_attaches_components(tmp_path, monkeypatch):
    world = _setup_world()
    roles_yaml = tmp_path / "roles.yaml"
    roles_yaml.write_text(
        """merchant:\n  can_request_abilities: false\n  uses_llm: false\n  fixed_abilities:\n    - TradeAbility\n""",
        encoding="utf-8",
    )
    monkeypatch.setattr(commands, "ROLES_PATH", roles_yaml)
    entity_id = commands.spawn(world, "npc:merchant")
    role = world.component_manager.get_component(entity_id, RoleComponent)
    assert role is not None
    assert role.role_name == "merchant"
    assert role.can_request_abilities is False
    assert role.uses_llm is False
    kab = world.component_manager.get_component(entity_id, KnownAbilitiesComponent)
    assert kab is not None
    assert kab.known_class_names == ["TradeAbility"]
