import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_world.persistence.event_log import EventLog, append_event, iter_events
import agent_world.persistence.event_log as evlog
import gzip
import json


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


def test_log_rotation(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "events.jsonl"
    monkeypatch.setattr(evlog, "_log_retention_bytes", lambda: 100)
    for i in range(3):
        append_event(path, i, "test", {"n": i})

    gz_files = [p for p in tmp_path.iterdir() if p.suffix == ".gz"]
    assert len(gz_files) == 1
    with gzip.open(gz_files[0], "rt", encoding="utf-8") as fh:
        rotated = [json.loads(l) for l in fh if l.strip()]
    assert [e["tick"] for e in rotated] == [0, 1]
    remaining = list(iter_events(path))
    assert len(remaining) == 1 and remaining[0]["tick"] == 2
