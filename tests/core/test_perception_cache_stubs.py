from agent_world.core.components.perception_cache import PerceptionCache


def test_perception_cache_default_state():
    cache = PerceptionCache()
    assert cache.visible_ability_uses == []
