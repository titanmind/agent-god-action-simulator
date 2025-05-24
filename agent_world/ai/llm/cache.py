"""Simple in-memory LRU cache for LLM prompts."""

from __future__ import annotations

from collections import OrderedDict
from typing import OrderedDict as OrderedDictType


class LLMCache:
    """LRU cache keyed by prompt strings."""

    def __init__(self, capacity: int = 1000) -> None:
        self.capacity = capacity
        self._store: OrderedDictType[str, str] = OrderedDict()

    # ------------------------------------------------------------------
    # Basic operations
    # ------------------------------------------------------------------
    def get(self, prompt: str) -> str | None:
        """Return cached response for ``prompt`` or ``None``."""

        if prompt in self._store:
            value = self._store.pop(prompt)
            self._store[prompt] = value
            return value
        return None

    def put(self, prompt: str, response: str) -> None:
        """Insert ``prompt`` → ``response`` pair, evicting LRU if needed."""

        if prompt in self._store:
            self._store.pop(prompt)
        elif len(self._store) >= self.capacity:
            self._store.popitem(last=False)
        self._store[prompt] = response

    def __contains__(self, prompt: str) -> bool:  # pragma: no cover - trivial
        return prompt in self._store

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._store)


__all__ = ["LLMCache"]
