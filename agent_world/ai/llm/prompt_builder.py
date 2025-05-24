"""Utilities for constructing deterministic LLM prompts."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, List


def _get_memories(agent_id: int, k: int) -> List[str]:
    """Return ``k`` memory snippets for ``agent_id`` or an empty list."""

    try:  # Import lazily so tests without memory module still run
        from ..memory import retrieve
    except Exception:  # pragma: no cover - memory module optional
        return []

    try:
        memories = retrieve(agent_id, k)
        if isinstance(memories, list):
            return [str(m) for m in memories]
    except Exception:  # pragma: no cover - retrieval failure
        pass
    return []


def _normalize(obj: Any) -> Any:
    """Recursively convert dataclasses to plain structures."""

    if is_dataclass(obj):
        return {k: _normalize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize(v) for v in obj]
    return obj


def build_prompt(agent_id: int, world_view: Any, *, memory_k: int = 5) -> str:
    """Return a deterministic prompt string for ``agent_id``.

    ``world_view`` should be composed of JSON-serialisable types or dataclasses
    thereof. ``memory_k`` controls how many past memory snippets to include. The
    output is deterministic for identical inputs to support replaying LLM
    interactions.
    """

    normalized = _normalize(world_view)
    serialized = json.dumps(normalized, sort_keys=True, indent=2)

    memories = _get_memories(agent_id, memory_k)
    mem_section = ""
    if memories:
        mem_json = json.dumps(memories, sort_keys=True, indent=2)
        mem_section = f"\nMemory:\n{mem_json}"

    header = (
        f"Agent {agent_id}, based on the following world view decide your next "
        "action."
    )
    prompt = f"{header}\nWorld View:\n{serialized}{mem_section}\nRespond with a single action"
    return prompt


__all__ = ["build_prompt"]
