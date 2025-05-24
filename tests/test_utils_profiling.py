from pathlib import Path
import pstats

import asyncio

from agent_world.utils.profiling import profile_ticks, profile_async


def test_profile_ticks_creates_dump(tmp_path: Path) -> None:
    calls: list[int] = []

    def tick() -> None:
        calls.append(1)

    out = tmp_path / "prof.prof"
    stats = profile_ticks(3, tick, out)

    assert out.exists()
    assert isinstance(stats, pstats.Stats)
    assert len(calls) == 3


def test_profile_async_creates_dump(tmp_path: Path) -> None:
    calls: list[int] = []

    async def tick() -> None:
        calls.append(1)

    out = tmp_path / "prof_async.prof"
    stats = asyncio.run(profile_async(3, tick, out))

    assert out.exists()
    assert isinstance(stats, pstats.Stats)
    assert len(calls) == 3
