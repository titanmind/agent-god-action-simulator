from agent_world.core.components.event_log import EventLog, MAX_RECENT_EVENTS
from agent_world.core.events import AbilityUseEvent


def test_event_log_trims_to_limit():
    log = EventLog()
    for i in range(MAX_RECENT_EVENTS + 5):
        log.recent.append(
            AbilityUseEvent(caster_id=i, ability_name=str(i), target_id=None, tick=i)
        )
    assert len(log.recent) == MAX_RECENT_EVENTS
    # Oldest events should be discarded
    first = next(iter(log.recent))
    assert first.caster_id == 5
