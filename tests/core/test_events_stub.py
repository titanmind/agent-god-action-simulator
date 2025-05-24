from agent_world.core.events import AbilityUseEvent


def test_ability_use_event_fields():
    event = AbilityUseEvent(caster_id=1, ability_name="Fireball", target_id=2, tick=42)
    assert event.caster_id == 1
    assert event.ability_name == "Fireball"
    assert event.target_id == 2
    assert event.tick == 42
