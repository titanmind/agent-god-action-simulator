"""Execution sandbox for dynamic ability code."""

from __future__ import annotations

import math
import signal
from types import MappingProxyType
from typing import Any, Dict

from RestrictedPython import compile_restricted
from RestrictedPython import safe_builtins


_ALLOWED_IMPORTS = {"math"}


class SandboxError(Exception):
    """Base error for sandbox execution."""


class SandboxImportError(SandboxError, ImportError):
    """Raised when a disallowed module is imported."""


class SandboxTimeoutError(SandboxError, TimeoutError):
    """Raised when the executed code exceeds the time limit."""


def _limited_import(
    name: str,
    globals: dict | None = None,
    locals: dict | None = None,
    fromlist: tuple | None = None,
    level: int = 0,
) -> Any:
    """Allow only importing modules listed in ``_ALLOWED_IMPORTS``."""

    if name in _ALLOWED_IMPORTS:
        return __import__(name, globals, locals, fromlist, level)
    raise SandboxImportError(f"import of '{name}' is not allowed")


def run_in_sandbox(
    code_str: str, /, extra_globals: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Execute ``code_str`` safely and return its globals mapping.

    Parameters
    ----------
    code_str:
        Python source code to execute.
    extra_globals:
        Additional variables to expose to the code.

    The code runs with RestrictedPython and may import only ``math``. Execution
    is aborted if it does not finish within 50 milliseconds.
    """

    compiled = compile_restricted(code_str, filename="<sandbox>", mode="exec")

    builtins_copy = dict(safe_builtins)
    builtins_copy["__import__"] = _limited_import

    globals_dict: Dict[str, Any] = {
        "__builtins__": MappingProxyType(builtins_copy),
        "math": math,
    }
    if extra_globals:
        globals_dict.update(extra_globals)

    def _timeout_handler(
        signum: int, frame: Any
    ) -> None:  # pragma: no cover - OS dependent
        raise SandboxTimeoutError("sandbox execution timed out")

    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, 0.05)
    try:
        exec(compiled, globals_dict)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)

    return globals_dict


__all__ = [
    "SandboxError",
    "SandboxImportError",
    "SandboxTimeoutError",
    "run_in_sandbox",
]
