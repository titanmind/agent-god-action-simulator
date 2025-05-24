"""Utilities for constructing deterministic LLM prompts."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _normalize(obj: Any) -> Any:
    """Recursively convert dataclasses to plain structures."""

    if is_dataclass(obj):
        return {k: _normalize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize(v) for v in obj]
    return obj


def build_prompt(agent_id: int, world_view: Any) -> str:
    """Return a deterministic prompt string for ``agent_id``.

    ``world_view`` should be composed of JSON-serialisable types or dataclasses
    thereof. The output is deterministic for identical inputs to support
    replaying LLM interactions.
    """

    normalized = _normalize(world_view)
    serialized = json.dumps(normalized, sort_keys=True, indent=2)
    header = (
        f"Agent {agent_id}, based on the following world view decide your next "
        "action."
    )
    prompt = f"{header}\nWorld View:\n{serialized}\nRespond with a single action"
    return prompt


__all__ = ["build_prompt"]
