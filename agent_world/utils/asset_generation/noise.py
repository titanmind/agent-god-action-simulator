"""Simple noise generation helpers."""

from __future__ import annotations

from random import Random


def threshold_mask(
    data: list[list[float]], threshold: float
) -> list[list[bool]]:
    """Return boolean grid where ``True`` indicates ``value >= threshold``."""

    mask: list[list[bool]] = []
    for row in data:
        mask.append([value >= threshold for value in row])
    return mask


def white_noise(
    width: int, height: int, seed: int | None = None
) -> list[list[float]]:
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


__all__ = ["white_noise", "threshold_mask"]
