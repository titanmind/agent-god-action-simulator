import pytest
from agent_world.main import bootstrap


def test_world_boots_without_entities():
    world = bootstrap(config_path="config.yaml")
    assert len(world.entity_manager.all_entities) == 0

