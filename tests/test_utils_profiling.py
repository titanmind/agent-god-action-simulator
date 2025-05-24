from pathlib import Path
import pstats

from agent_world.utils.profiling import profile_ticks


def test_profile_ticks_creates_dump(tmp_path: Path) -> None:
    calls: list[int] = []

    def tick() -> None:
        calls.append(1)

    out = tmp_path / "prof.prof"
    stats = profile_ticks(3, tick, out)

    assert out.exists()
    assert isinstance(stats, pstats.Stats)
    assert len(calls) == 3
