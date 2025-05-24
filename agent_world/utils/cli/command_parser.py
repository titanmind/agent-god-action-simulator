"""Simple command parsing utilities for the development CLI."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Callable
import threading
import queue # For thread-safe command passing

# ---------------------------------------------------------------------------
# Cross-platform helpers for “is there console input waiting?”
# ---------------------------------------------------------------------------

if os.name == "nt":  # Windows ──────────────────────────────────────────────
    import msvcrt  # type: ignore  # std-lib on Windows only

    # For threaded input, we don't need _stdin_ready or _read_line here directly
    # The thread will block on input, which is fine for a separate thread.

else:  # POSIX (Linux, macOS, …) ────────────────────────────────────────────
    import select
    # POSIX can also use blocking input in a thread.
    # select-based non-blocking is more for single-threaded scenarios.


# ---------------------------------------------------------------------------
# Core CLI machinery
# ---------------------------------------------------------------------------

@dataclass
class CLICommand:
    """Result of parsing a command string."""
    name: str
    args: List[str]


_cli_command_queue: queue.Queue[CLICommand] = queue.Queue()
_cli_thread_stop_event = threading.Event()


def _cli_input_thread_func():
    """Thread function to read CLI input."""
    print("CLI input thread started. Type commands prefixed with '/' and press Enter.")
    while not _cli_thread_stop_event.is_set():
        try:
            # sys.stdin.readline() is blocking, which is fine in a dedicated thread.
            line = sys.stdin.readline()
            if not line: # EOF, e.g., if stdin is closed
                if _cli_thread_stop_event.is_set(): # Expected if stopping
                    break
                print("CLI input stream closed unexpectedly.")
                break # Exit thread if stdin closes

            line = line.strip()
            if line: # Only process non-empty lines
                parsed = parse_command(line)
                if parsed:
                    _cli_command_queue.put(parsed)
        except KeyboardInterrupt:
            print("CLI thread interrupted. Use /quit in main app or close window.")
            # Let main thread handle shutdown via running flag
            break
        except Exception as e:
            print(f"Error in CLI input thread: {e}")
            # Potentially break or sleep to avoid spamming errors
            if _cli_thread_stop_event.is_set(): break # Exit if stopping
            threading.Event().wait(1.0) # Wait a bit before retrying

    print("CLI input thread stopped.")


def start_cli_thread():
    """Starts the CLI input thread."""
    if _cli_thread_stop_event.is_set(): # If previously stopped, reset
        _cli_thread_stop_event.clear()

    thread = threading.Thread(target=_cli_input_thread_func, daemon=True, name="CLIInputThread")
    thread.start()
    return thread

def stop_cli_thread():
    """Signals the CLI input thread to stop."""
    _cli_thread_stop_event.set()
    # To fully unblock readline on POSIX, you might need to write to stdin or close it.
    # On Windows, msvcrt might not need this as much, but it's good practice.
    # This is tricky. A simpler way is just letting the daemon thread exit when the main app exits.
    print("CLI input thread stop signal sent.")


def parse_command(text: str) -> Optional[CLICommand]:
    """Return a :class:`CLICommand` from ``text`` if it starts with ``/``."""
    text = text.strip()
    if not text.startswith("/"):
        return None
    parts = text[1:].split()
    if not parts:
        return None

    cmd = parts[0].lower()

    if cmd == "follow":
        return CLICommand(name="follow", args=parts[1:2])

    return CLICommand(name=cmd, args=parts[1:])


def poll_command() -> Optional[CLICommand]:
    """Return a command from the internal queue if available, else ``None``."""
    try:
        return _cli_command_queue.get_nowait()
    except queue.Empty:
        return None


__all__ = ["CLICommand", "parse_command", "poll_command", "start_cli_thread", "stop_cli_thread"]