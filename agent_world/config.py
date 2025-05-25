"""Simple configuration loader for agent_world."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


@dataclass
class WorldConfig:
    """Configuration values for the world section."""

    size: tuple[int, int] = (100, 100)
    tick_rate: float = 10.0
    max_entities: int = 8000
    paused_for_angel_timeout_seconds: int = 60


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""

    mode: str = "offline"
    agent_decision_model: str = "default/model"
    angel_generation_model: str = "default/model"


@dataclass
class Config:
    """Top level configuration dataclass."""

    world: WorldConfig
    llm: LLMConfig
    paths: Optional[Dict[str, str]] = None
    cache: Optional[Dict[str, Any]] = None


def _parse_config(data: dict[str, Any]) -> Config:
    """Convert raw ``data`` into :class:`Config`."""

    world_data = data.get("world", {})
    world = WorldConfig(
        size=tuple(world_data.get("size", [100, 100])),
        tick_rate=float(world_data.get("tick_rate", 10)),
        max_entities=int(world_data.get("max_entities", 8000)),
        paused_for_angel_timeout_seconds=int(
            world_data.get("paused_for_angel_timeout_seconds", 60)
        ),
    )

    llm_data = data.get("llm", {})
    llm = LLMConfig(
        mode=llm_data.get("mode", "offline"),
        agent_decision_model=llm_data.get("agent_decision_model", "default/model"),
        angel_generation_model=llm_data.get("angel_generation_model", "default/model"),
    )

    paths = data.get("paths")
    cache = data.get("cache")

    return Config(world=world, llm=llm, paths=paths, cache=cache)


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Load configuration from ``path`` and return a :class:`Config`."""

    if path.is_file():
        raw = yaml.safe_load(path.read_text()) or {}
    else:
        raw = {}
    return _parse_config(raw)


# Load configuration at module import time.
CONFIG = load_config()


__all__ = [
    "CONFIG",
    "Config",
    "WorldConfig",
    "LLMConfig",
    "load_config",
]

