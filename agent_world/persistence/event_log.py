from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List


def append_event(
    dest: str | Path | List[Dict[str, Any]], tick: int, event_type: str, data: Any
) -> None:
    """Append an event to ``dest`` which may be a path or in-memory list."""

    event = {"tick": tick, "event_type": event_type, "data": data}
    if isinstance(dest, list):
        dest.append(event)
        return

    p = Path(dest)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def iter_events(path: str | Path) -> Iterator[Dict[str, Any]]:
    """Yield events from ``path`` in the order they were logged."""

    p = Path(path)
    if not p.exists():
        return

    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield event


class EventLog:
    """Convenience wrapper around :func:`append_event` and :func:`iter_events`."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, tick: int, event_type: str, data: Any) -> None:
        append_event(self.path, tick, event_type, data)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        yield from iter_events(self.path)


__all__ = ["EventLog", "append_event", "iter_events"]
