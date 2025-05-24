"""Simple command parsing utilities for the development CLI."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional

# ---------------------------------------------------------------------------
# Cross-platform helpers for “is there console input waiting?”
# ---------------------------------------------------------------------------

if os.name == "nt":  # Windows ──────────────────────────────────────────────
    import msvcrt  # type: ignore  # std-lib on Windows only

    def _stdin_ready() -> bool:  # noqa: D401
        """Return True if a key is waiting on the Windows console."""
        return msvcrt.kbhit()

    def _read_line() -> str:  # noqa: D401
        """Read a full line from the Windows console without blocking."""
        buf: List[str] = []
        while True:
            ch = msvcrt.getwch()  # wide-char read
            if ch in ("\r", "\n"):
                break
            buf.append(ch)
        return "".join(buf) + "\n"

else:  # POSIX (Linux, macOS, …) ────────────────────────────────────────────
    import select

    def _stdin_ready() -> bool:  # noqa: D401
        """Return True if stdin has data ready (non-blocking)."""
        try:
            return bool(select.select([sys.stdin], [], [], 0)[0])
        except OSError:
            # stdin might be a pipe or closed in headless CI runs
            return False

    def _read_line() -> str:  # noqa: D401
        """Read a full line from stdin."""
        return sys.stdin.readline()


# ---------------------------------------------------------------------------
# Core CLI machinery
# ---------------------------------------------------------------------------

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
    """Return a command from console input if available, else ``None``."""

    if _stdin_ready():
        line = _read_line()
        return parse_command(line)
    return None


__all__ = ["CLICommand", "parse_command", "poll_command"]
