import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.persistence.event_log import EventLog, append_event, iter_events


def test_append_and_iter_events(tmp_path: Path) -> None:
    log = tmp_path / "events.jsonl"
    append_event(log, 1, "attack", {"damage": 5})
    append_event(log, 2, "move", {"dx": 1})
    events = list(iter_events(log))
    assert events == [
        {"tick": 1, "event_type": "attack", "data": {"damage": 5}},
        {"tick": 2, "event_type": "move", "data": {"dx": 1}},
    ]


def test_event_log_class(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    log = EventLog(path)
    log.append(0, "start", {})
    log.append(1, "end", {"ok": True})
    assert list(log) == [
        {"tick": 0, "event_type": "start", "data": {}},
        {"tick": 1, "event_type": "end", "data": {"ok": True}},
    ]


def test_iter_events_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    assert list(iter_events(path)) == []
