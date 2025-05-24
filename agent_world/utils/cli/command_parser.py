"""Simple command parsing utilities for the development CLI."""

from __future__ import annotations

import select
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CLICommand:
    """Result of parsing a command string."""

    name: str
    args: List[str]


def parse_command(text: str) -> Optional[CLICommand]:
    """Return a :class:`CLICommand` from ``text`` if it starts with ``/``."""

    text = text.strip()
    if not text.startswith("/"):
        return None
    parts = text[1:].split()
    if not parts:
        return None
    return CLICommand(name=parts[0].lower(), args=parts[1:])


def poll_command() -> Optional[CLICommand]:
    """Return a command from ``stdin`` if available, else ``None``."""

    if select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        return parse_command(line)
    return None


__all__ = ["CLICommand", "parse_command", "poll_command"]
