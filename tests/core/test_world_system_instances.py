from agent_world.main import bootstrap


def test_combat_system_instance_attached():
    world = bootstrap(config_path="config.yaml")
    assert getattr(world, "combat_system_instance", None) is not None
