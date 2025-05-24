import pytest

from agent_world.utils.sandbox import (
    run_in_sandbox,
    SandboxImportError,
    SandboxTimeoutError,
)


def test_sandbox_allows_math():
    env = run_in_sandbox("result = math.sqrt(16)")
    assert env["result"] == 4.0


def test_sandbox_blocks_imports():
    with pytest.raises(SandboxImportError):
        run_in_sandbox("import os\n")


def test_sandbox_timeout():
    code = "while True:\n    pass"
    with pytest.raises(SandboxTimeoutError):
        run_in_sandbox(code)
