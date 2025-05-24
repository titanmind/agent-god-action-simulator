"""Simple noise generation helpers."""

from __future__ import annotations

from random import Random


def white_noise(width: int, height: int, seed: int | None = None) -> list[list[float]]:
    """Return ``height`` × ``width`` grid of random floats in ``[0, 1)``.

    Parameters
    ----------
    width:
        Number of columns in the generated grid.
    height:
        Number of rows in the generated grid.
    seed:
        Optional seed for deterministic output.
    """

    rnd = Random(seed)
    return [[rnd.random() for _ in range(width)] for _ in range(height)]


__all__ = ["white_noise"]
