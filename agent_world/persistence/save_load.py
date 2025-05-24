"""Load and save world snapshots."""

from __future__ import annotations

import json
import gzip
from pathlib import Path

from .serializer import world_from_dict, world_to_dict


def save_world(world: "World", path: str | Path, *, gzip_compress: bool = True) -> None:
    """Write ``world`` state to ``path`` as JSON.

    Parameters
    ----------
    world:
        The :class:`~agent_world.core.world.World` instance to serialize.
    path:
        Destination file path.
    gzip_compress:
        If ``True`` (default), compress the JSON using gzip.
    """

    data = world_to_dict(world)
    text = json.dumps(data, indent=2)
    path = Path(path)
    if gzip_compress:
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(text)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


def load_world(path: str | Path, *, gzip_compress: bool = True) -> "World":
    """Read world state from ``path`` and return a new :class:`World` instance."""

    path = Path(path)
    if gzip_compress:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    return world_from_dict(data)


__all__ = ["save_world", "load_world"]
