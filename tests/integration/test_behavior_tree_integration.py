import pytest
from agent_world.main import bootstrap
from agent_world.utils.cli import commands
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.systems.ai.behavior_tree_system import BehaviorTreeSystem


def test_behavior_tree_system_integration(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("world:\n  size: [5, 5]\n")

    world = bootstrap(config_path=cfg)

    creature_id = commands.spawn(world, "npc:creature", "1", "1")

    target_id = world.entity_manager.create_entity()
    cm = world.component_manager
    cm.add_component(target_id, Position(2, 1))
    cm.add_component(target_id, Health(cur=10, max=10))
    world.spatial_index.insert(target_id, (2, 1))

    world.time_manager.tick_counter = 0
    world.systems_manager.update(world, world.time_manager.tick_counter)

    assert any(isinstance(s, BehaviorTreeSystem) for s in world.systems_manager._systems)
    assert world.raw_actions_with_actor
    actor, action = world.raw_actions_with_actor[0]
    assert actor == creature_id
    assert action.startswith("USE_ABILITY") or action.startswith("MOVE")
