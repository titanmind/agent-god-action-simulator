from __future__ import annotations

import json
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List

import yaml

# Event type constants used by various systems
LLM_REQUEST = "LLM_REQUEST"
LLM_RESPONSE = "LLM_RESPONSE"
ANGEL_ACTION = "ANGEL_ACTION"
COMBAT_ATTACK = "COMBAT_ATTACK"
COMBAT_DEATH = "COMBAT_DEATH"
CRAFT = "CRAFT"


def _log_retention_bytes() -> int:
    """Return log rotation threshold in bytes from ``config.yaml``."""
    path = Path(__file__).resolve().parents[2] / "config.yaml"
    default_mb = 50
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh) or {}
            default_mb = int(cfg.get("cache", {}).get("log_retention_mb", default_mb))
        except Exception:
            pass
    return default_mb * 1024 * 1024


def _rotate_log(path: Path) -> None:
    """Compress ``path`` and clear it for new events."""
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    rotated = path.with_name(f"{path.stem}_{ts}{path.suffix}")
    path.rename(rotated)
    gz_path = rotated.with_suffix(rotated.suffix + ".gz")
    with open(rotated, "rb") as src, gzip.open(gz_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
    rotated.unlink()


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

    if p.exists() and p.stat().st_size >= _log_retention_bytes():
        _rotate_log(p)

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


__all__ = [
    "EventLog",
    "append_event",
    "iter_events",
    "LLM_REQUEST",
    "LLM_RESPONSE",
    "ANGEL_ACTION",
    "COMBAT_ATTACK",
    "COMBAT_DEATH",
    "CRAFT",
]
