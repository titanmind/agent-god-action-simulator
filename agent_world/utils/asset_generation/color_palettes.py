"""Deterministic colour palette generation helpers."""

from __future__ import annotations

import colorsys
import hashlib
from random import Random


def _seed_from_name(name: str) -> int:
    """Return a stable integer seed derived from ``name``."""

    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _hsv_to_rgb_int(h: float, s: float, v: float) -> tuple[int, int, int]:
    """Convert HSV floats in ``[0, 1]`` to RGB integer tuple."""

    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def get_palette(faction: str, n: int) -> list[tuple[int, int, int]]:
    """Return ``n`` RGB colours derived from ``faction`` seed."""

    if n <= 0:
        return []

    rnd = Random(_seed_from_name(faction))
    base = rnd.random()
    palette: list[tuple[int, int, int]] = []
    for i in range(n):
        hue = (base + i / n) % 1.0
        sat = 0.6 + rnd.random() * 0.4
        val = 0.8 + rnd.random() * 0.2
        palette.append(_hsv_to_rgb_int(hue, sat, val))
    return palette


__all__ = ["get_palette"]
