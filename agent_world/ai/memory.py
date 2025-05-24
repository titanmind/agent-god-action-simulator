"""Lightweight per-agent short-term memory store."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List


@dataclass
class MemoryEntry:
    """Single memory snippet and its naive embedding."""

    text: str
    vector: List[float]


def _embed(text: str) -> List[float]:
    """Return a tiny embedding for ``text``.

    The implementation is intentionally simple and deterministic to keep
    dependencies minimal. It just maps characters to an averaged value.
    """

    if not text:
        return [0.0]
    total = sum(ord(ch) for ch in text)
    return [total / len(text)]


class ShortTermMemory:
    """Ring-buffer memory store keyed by ``agent_id``."""

    def __init__(self, capacity: int = 64) -> None:
        self.capacity = capacity
        self._store: Dict[int, Deque[MemoryEntry]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def store(self, agent_id: int, snippet: str) -> None:
        """Insert ``snippet`` for ``agent_id``, pruning oldest if needed."""

        ring = self._store.setdefault(agent_id, deque(maxlen=self.capacity))
        entry = MemoryEntry(snippet, _embed(snippet))
        ring.append(entry)

    def retrieve(self, agent_id: int, k: int) -> List[str]:
        """Return up to ``k`` most recent snippets for ``agent_id``."""

        ring = self._store.get(agent_id)
        if not ring:
            return []
        k = max(0, k)
        entries = list(ring)[-k:][::-1]
        return [entry.text for entry in entries]


__all__ = ["ShortTermMemory", "MemoryEntry"]
